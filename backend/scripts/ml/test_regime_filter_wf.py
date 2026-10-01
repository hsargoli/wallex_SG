import os
import sys
import asyncio
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

# Ensure backend root is in PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.getcwd())

from app.application.use_cases.get_candles import GetCandlesUseCase
from app.core.config import get_settings
from app.infrastructure.exchange.wallex.client import WallexExchange
from app.services.bottom_detector import detect_bottom
from app.services.regime_detector import detect_regime
from app.services.ml_bottom_model import candles_to_df, build_features, load_model

SYMBOLS = ["BTCTMN", "ETHTMN", "XRPTMN", "DOGETMN", "SOLTMN"]
TF = "15m"
N_CANDLES = 2000

WARMUP = 100
TP_PCT = 2.0
SL_PCT = 1.5
FEE_PCT = 0.2
MAX_DURATION = 24

RULE_MIN_SCORE = 5
ML_STRONG = 0.55

REGIME_LOOKBACK = 200
REGIME_REFRESH = 50


@dataclass
class Trade:
    symbol: str
    entry_idx: int
    exit_idx: int
    ret_pct: float


@dataclass
class Stats:
    name: str
    trades: List[Trade] = field(default_factory=list)

    def add(self, trade: Trade) -> None:
        self.trades.append(trade)

    @property
    def total(self) -> int:
        return len(self.trades)

    @property
    def wins(self) -> int:
        return sum(1 for t in self.trades if t.ret_pct > 0)

    @property
    def losses(self) -> int:
        return sum(1 for t in self.trades if t.ret_pct <= 0)

    @property
    def wr(self) -> float:
        return (self.wins / self.total * 100) if self.total else 0.0

    @property
    def total_return(self) -> float:
        if not self.trades:
            return 0.0
        eq = 1.0
        for t in self.trades:
            eq *= (1 + t.ret_pct / 100)
        return (eq - 1) * 100


def _dynamic_tp_sl(regime, base_tp: float, base_sl: float) -> Tuple[float, float]:
    tp, sl = base_tp, base_sl
    name = str(getattr(regime, "name", "") or getattr(regime, "regime", "") or getattr(regime, "label", "")).lower()

    if any(k in name for k in ["up", "bull", "trend_up"]):
        tp = base_tp * 1.5   # 3.0%
        sl = base_sl * 1.0   # 1.5%
    elif any(k in name for k in ["down", "bear", "trend_down"]):
        tp = base_tp * 0.8   # 1.6%
        sl = base_sl * 1.2   # 1.8%
    else:
        # Range / Choppy
        tp = base_tp * 0.9   # 1.8%
        sl = base_sl * 0.9   # 1.35%

    return float(tp), float(sl)


def _exit_price_conservative(candle, tp_price: float, sl_price: float) -> Optional[float]:
    hit_tp = candle.high >= tp_price
    hit_sl = candle.low <= sl_price

    if hit_tp and hit_sl:
        return sl_price  # Conservative: assume SL hit first
    if hit_sl:
        return sl_price
    if hit_tp:
        return tp_price
    return None


def _build_ml_probs(candles, model) -> List[Optional[float]]:
    df = candles_to_df(candles)
    X_all = build_features(df)

    ml_probs: List[Optional[float]] = [None] * len(X_all)
    valid_mask = ~X_all.isna().any(axis=1)
    if valid_mask.sum() > 0:
        probs = model.predict_proba(X_all[valid_mask])[:, 1]
        for i, idx in enumerate(X_all[valid_mask].index):
            ml_probs[int(idx)] = float(probs[i])
    return ml_probs


def run_backtest_window(
    symbol: str,
    candles: list,
    model,
    start_idx: int,
    end_idx: int,
    *,
    use_regime_filter: bool,
    use_dynamic_tp_sl: bool,
) -> Tuple[Stats, Dict[str, int]]:
    stats = Stats(name=symbol)
    counters = {"regime_blocked": 0, "signals": 0, "entries": 0}

    ml_probs = _build_ml_probs(candles, model)

    open_pos = None
    last_regime = None
    last_regime_idx = None

    for idx in range(max(WARMUP, start_idx), min(end_idx, len(candles))):
        candle = candles[idx]

        # Check exits
        if open_pos is not None:
            exit_price = _exit_price_conservative(candle, open_pos["tp"], open_pos["sl"])
            if exit_price is None and idx - open_pos["entry_idx"] >= MAX_DURATION:
                exit_price = float(candle.close)

            if exit_price is not None:
                ret = (float(exit_price) / open_pos["entry"] - 1) * 100 - FEE_PCT
                stats.add(Trade(symbol=symbol, entry_idx=open_pos["entry_idx"], exit_idx=idx, ret_pct=ret))
                open_pos = None

        if open_pos is not None:
            continue

        # Stateful regime check
        if use_regime_filter:
            refresh = (last_regime is None) or (last_regime_idx is None) or (idx - last_regime_idx >= REGIME_REFRESH)
            if refresh:
                recent = candles[: idx + 1][-REGIME_LOOKBACK:]
                last_regime = detect_regime(recent)
                last_regime_idx = idx

            if not getattr(last_regime, "is_tradeable", True):
                counters["regime_blocked"] += 1
                continue

        # Entry signal check
        ml_prob = ml_probs[idx]
        rule = detect_bottom(candles, idx=idx)

        should_enter = (
            (ml_prob is not None and ml_prob >= ML_STRONG)
            or (rule.is_bottom and rule.score >= RULE_MIN_SCORE)
        )
        if not should_enter:
            continue

        counters["signals"] += 1

        entry = float(candle.close)
        tp_pct, sl_pct = TP_PCT, SL_PCT
        if use_dynamic_tp_sl and use_regime_filter and last_regime is not None:
            tp_pct, sl_pct = _dynamic_tp_sl(last_regime, TP_PCT, SL_PCT)

        open_pos = {
            "entry": entry,
            "tp": entry * (1 + tp_pct / 100),
            "sl": entry * (1 - sl_pct / 100),
            "entry_idx": idx,
        }
        counters["entries"] += 1

    return stats, counters


def merge_stats(name: str, per_symbol: Dict[str, Stats]) -> Stats:
    merged = Stats(name=name)
    for s in per_symbol.values():
        merged.trades.extend(s.trades)
    return merged


def print_table(title: str, per_symbol: Dict[str, Stats]) -> None:
    total = merge_stats("TOTAL", per_symbol)
    print(f"\n{title}")
    print("─" * 78)
    print(f"{'SYMBOL':<10} {'TRADES':>7} {'W':>5} {'L':>5} {'WR%':>8} {'RETURN%':>12}")
    print("─" * 78)
    for sym in sorted(per_symbol.keys()):
        s = per_symbol[sym]
        print(f"{sym:<10} {s.total:>7} {s.wins:>5} {s.losses:>5} {s.wr:>7.1f}% {s.total_return:>11.2f}%")
    print("─" * 78)
    print(f"{'TOTAL':<10} {total.total:>7} {total.wins:>5} {total.losses:>5} {total.wr:>7.1f}% {total.total_return:>11.2f}%")


def walk_forward_splits(n: int, train: float, test: float, step: float) -> List[Tuple[int, int, int]]:
    train_n = int(n * train)
    test_n = int(n * test)
    step_n = max(1, int(n * step))

    splits = []
    train_end = train_n
    while True:
        test_start = train_end
        test_end = test_start + test_n
        if test_end > n:
            break
        splits.append((train_end, test_start, test_end))
        train_end += step_n
    return splits


async def fetch_all():
    settings = get_settings()
    async def one(sym):
        ex = WallexExchange.create(settings)
        try:
            uc = GetCandlesUseCase(exchange=ex)
            return sym, await uc.execute(symbol=sym, timeframe=TF, limit=N_CANDLES)
        except Exception:
            return sym, []
        finally:
            await ex.aclose()

    results = await asyncio.gather(*[one(s) for s in SYMBOLS])
    return {s: c for s, c in results if c}


async def main():
    print(f"📥 Fetching {len(SYMBOLS)} symbols × {TF}...")
    markets_data = await fetch_all()
    print(f"✅ Loaded {len(markets_data)} symbols\n")

    print("🧠 Loading model...")
    try:
        model = load_model()
        print("✅ Model loaded\n")
    except Exception as e:
        print(f"❌ Failed to load model: {e}")
        return

    # Walk-forward splits (expanding train 60%, test 20%, step 20%)
    train_ratio, test_ratio, step_ratio = 0.6, 0.2, 0.2

    modes = [
        ("A) NO_FILTER (Baseline Out-of-Sample)", dict(use_regime_filter=False, use_dynamic_tp_sl=False)),
        ("B) REGIME_FILTER (Stateful Gating)", dict(use_regime_filter=True, use_dynamic_tp_sl=False)),
        ("C) REGIME + DYNAMIC TP/SL", dict(use_regime_filter=True, use_dynamic_tp_sl=True)),
    ]

    for mode_name, mode_kwargs in modes:
        print("\n" + "=" * 80)
        print(f"🚀 MODE: {mode_name}")
        print("=" * 80)

        wf_per_symbol: Dict[str, Stats] = {s: Stats(name=s) for s in markets_data.keys()}
        wf_counters: Dict[str, Dict[str, int]] = {s: {"regime_blocked": 0, "signals": 0, "entries": 0} for s in markets_data.keys()}

        for symbol, candles in markets_data.items():
            splits = walk_forward_splits(len(candles), train=train_ratio, test=test_ratio, step=step_ratio)
            for (_, test_start, test_end) in splits:
                s_window, c_window = run_backtest_window(
                    symbol=symbol,
                    candles=candles,
                    model=model,
                    start_idx=test_start,
                    end_idx=test_end,
                    **mode_kwargs,
                )
                wf_per_symbol[symbol].trades.extend(s_window.trades)
                for k in wf_counters[symbol].keys():
                    wf_counters[symbol][k] += int(c_window.get(k, 0))

        print_table(f"📊 Results for {mode_name}", wf_per_symbol)

        if mode_kwargs["use_regime_filter"]:
            print("\n🔍 Execution Breakdown (Blocked / Signals / Entries):")
            for sym in sorted(wf_counters.keys()):
                c = wf_counters[sym]
                print(f"  {sym:<10} Blocked Candles: {c['regime_blocked']:<4} | Valid Signals: {c['signals']:<3} | Filled: {c['entries']}")


if __name__ == "__main__":
    asyncio.run(main())
