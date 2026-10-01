import os
import sys
import asyncio
from dataclasses import dataclass, field
from typing import Dict, List, Optional

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.getcwd())

from app.application.use_cases.get_candles import GetCandlesUseCase
from app.core.config import get_settings
from app.infrastructure.exchange.wallex.client import WallexExchange
from app.services.bottom_detector import detect_bottom
from app.services.ml_bottom_model import candles_to_df, build_features, load_model

SYMBOLS = ["BTCTMN", "ETHTMN", "XRPTMN", "DOGETMN", "SOLTMN"]
TF = "15m"
N_CANDLES = 2000

TP_PCT = 2.0
SL_PCT = 1.5
FEE_PCT = 0.2
MAX_DURATION = 24  # 24 * 15m = 6 hours max hold

RULE_MIN_SCORE = 5
ML_STRONG = 0.55


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


def _exit_price_conservative(candle, tp_price: float, sl_price: float) -> Optional[float]:
    hit_tp = candle.high >= tp_price
    hit_sl = candle.low <= sl_price
    if hit_tp and hit_sl:
        return sl_price  # Worst case assumption
    if hit_sl:
        return sl_price
    if hit_tp:
        return tp_price
    return None


def run_slice_backtest(symbol: str, candles: list, model, start_idx: int, end_idx: int) -> Stats:
    stats = Stats(name=symbol)
    df = candles_to_df(candles)
    X_all = build_features(df)

    ml_probs: List[Optional[float]] = [None] * len(X_all)
    valid_mask = ~X_all.isna().any(axis=1)
    if valid_mask.sum() > 0:
        probs = model.predict_proba(X_all[valid_mask])[:, 1]
        for i, idx in enumerate(X_all[valid_mask].index):
            ml_probs[int(idx)] = float(probs[i])

    open_pos = None

    for idx in range(start_idx, end_idx):
        candle = candles[idx]

        # Check exits
        if open_pos is not None:
            exit_price = _exit_price_conservative(candle, open_pos["tp"], open_pos["sl"])
            if exit_price is None and (idx - open_pos["entry_idx"]) >= MAX_DURATION:
                exit_price = float(candle.close)

            if exit_price is not None:
                ret = (float(exit_price) / open_pos["entry"] - 1) * 100 - FEE_PCT
                stats.add(Trade(symbol=symbol, entry_idx=open_pos["entry_idx"], exit_idx=idx, ret_pct=ret))
                open_pos = None

        if open_pos is not None:
            continue

        # Check entry signals
        ml_prob = ml_probs[idx]
        rule = detect_bottom(candles, idx=idx)

        should_enter = (
            (ml_prob is not None and ml_prob >= ML_STRONG)
            or (rule.is_bottom and rule.score >= RULE_MIN_SCORE)
        )
        if not should_enter:
            continue

        entry = float(candle.close)
        open_pos = {
            "entry": entry,
            "tp": entry * (1 + TP_PCT / 100),
            "sl": entry * (1 - SL_PCT / 100),
            "entry_idx": idx,
        }

    return stats


def print_summary(title: str, results: Dict[str, Stats]):
    total_trades = sum(s.total for s in results.values())
    total_wins = sum(s.wins for s in results.values())
    total_losses = sum(s.losses for s in results.values())
    wr = (total_wins / total_trades * 100) if total_trades else 0.0
    tot_ret = sum(s.total_return for s in results.values())

    print(f"\n{title}")
    print("─" * 70)
    print(f"{'SYMBOL':<10} {'TRADES':>7} {'W':>5} {'L':>5} {'WR%':>8} {'RETURN%':>12}")
    print("─" * 70)
    for sym in sorted(results.keys()):
        s = results[sym]
        print(f"{sym:<10} {s.total:>7} {s.wins:>5} {s.losses:>5} {s.wr:>7.1f}% {s.total_return:>11.2f}%")
    print("─" * 70)
    print(f"{'TOTAL':<10} {total_trades:>7} {total_wins:>5} {total_losses:>5} {wr:>7.1f}% {tot_ret:>11.2f}%")


async def main():
    settings = get_settings()

    async def fetch(sym):
        ex = WallexExchange.create(settings)
        try:
            uc = GetCandlesUseCase(exchange=ex)
            return sym, await uc.execute(symbol=sym, timeframe=TF, limit=N_CANDLES)
        finally:
            await ex.aclose()

    print("📥 Loading market data...")
    raw = await asyncio.gather(*[fetch(s) for s in SYMBOLS])
    data = {s: c for s, c in raw if c}

    model = load_model()

    # 10 days = 960 candles (15m TF)
    # Window 1: 10 to 20 days ago (Historical Slice)
    # Window 2: Last 10 days (Recent Slice)

    print("\n" + "=" * 70)
    print("⏳ TEST 1: بازه ۱۰ روز قبل‌تر (کندل‌های ۱۰۰ تا ۱۰۰۰ — قدیمی‌تر)")
    print("=" * 70)
    hist_results = {s: run_slice_backtest(s, candles, model, start_idx=100, end_idx=1000) for s, candles in data.items()}
    print_summary("📊 نتیجه بازه ۱۰ روز قبل‌تر", hist_results)

    print("\n" + "=" * 70)
    print("⏳ TEST 2: بازه ۱۰ روز اخیر (کندل‌های ۱۰۰۰ تا ۲۰۰۰ — نزدیک به حال)")
    print("=" * 70)
    recent_results = {s: run_slice_backtest(s, candles, model, start_idx=1000, end_idx=len(candles)) for s, candles in data.items()}
    print_summary("📊 نتیجه بازه ۱۰ روز اخیر", recent_results)


if __name__ == "__main__":
    asyncio.run(main())
