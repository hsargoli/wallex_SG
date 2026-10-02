"""Backtest استراتژی کف‌خرید با ML + قوانین."""

import asyncio
from dataclasses import dataclass, field
from decimal import Decimal

from app.application.use_cases.get_candles import GetCandlesUseCase
from app.core.config import get_settings
from app.infrastructure.exchange.wallex.client import WallexExchange
from app.services.bottom_detector import detect_bottom
from app.services.ml_bottom_model import (
    build_features,
    candles_to_df,
    load_model,
)
from app.domain.entities.candle import Candle

SYMBOLS = ["BTCTMN", "ETHTMN", "XRPTMN", "DOGETMN", "SOLTMN"]
TIMEFRAME = "15m"
N_CANDLES = 1000
WARMUP = 200
TP_PCT = 3.0
SL_PCT = 1.5
MAX_DURATION = 24
FEE_PCT = 0.2  # کارمزد roundtrip

# آستانه‌ها
ML_STRONG = 0.55
RULE_MIN_SCORE = 5


async def fetch_all():
    settings = get_settings()
    async def one(sym):
        ex = WallexExchange.create(settings)
        try:
            uc = GetCandlesUseCase(exchange=ex)
            return sym, await uc.execute(symbol=sym, timeframe=TIMEFRAME, limit=N_CANDLES)
        except Exception:
            return sym, []
        finally:
            await ex.aclose()

    results = await asyncio.gather(*[one(s) for s in SYMBOLS])
    return {s: c for s, c in results if c}


def predict_prob_fast(model, features_row) -> float | None:
    """پیش‌بینی سریع روی یک row."""
    if features_row.isna().any():
        return None
    try:
        prob = model.predict_proba(features_row.to_frame().T)[0]
        return float(prob[1])
    except Exception:
        return None


@dataclass
class Trade:
    symbol: str
    entry_time: int
    exit_time: int
    entry_price: float
    exit_price: float
    return_pct: float
    exit_reason: str
    duration: int


@dataclass
class BacktestStats:
    name: str
    trades: list[Trade] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.trades)

    @property
    def wins(self) -> int:
        return sum(1 for t in self.trades if t.return_pct > 0)

    @property
    def losses(self) -> int:
        return sum(1 for t in self.trades if t.return_pct <= 0)

    @property
    def win_rate(self) -> float:
        return (self.wins / self.total * 100) if self.total else 0

    @property
    def total_return(self) -> float:
        if not self.trades:
            return 0
        # ترکیب ضربی
        eq = 1.0
        for t in self.trades:
            eq *= (1 + t.return_pct / 100)
        return (eq - 1) * 100

    @property
    def avg_win(self) -> float:
        w = [t.return_pct for t in self.trades if t.return_pct > 0]
        return sum(w) / len(w) if w else 0

    @property
    def avg_loss(self) -> float:
        l = [t.return_pct for t in self.trades if t.return_pct <= 0]
        return sum(l) / len(l) if l else 0


def run_one_strategy(
    name: str,
    markets_data: dict[str, list[Candle]],
    model,
    entry_checker,
) -> BacktestStats:
    """یک backtest کامل با منطق ورود مشخص."""
    stats = BacktestStats(name=name)

    for symbol, candles in markets_data.items():
        df = candles_to_df(candles)
        X_all = build_features(df)

        open_pos = None  # dict

        for idx in range(WARMUP, len(candles)):
            candle = candles[idx]

            # ---- چک خروج ----
            if open_pos is not None:
                exit_price = None
                reason = ""

                if candle.high >= open_pos["tp"]:
                    exit_price = open_pos["tp"]
                    reason = "tp"
                elif candle.low <= open_pos["sl"]:
                    exit_price = open_pos["sl"]
                    reason = "sl"
                elif idx - open_pos["entry_idx"] >= MAX_DURATION:
                    exit_price = candle.close
                    reason = "timeout"

                if exit_price is not None:
                    ret = (float(exit_price) / open_pos["entry"] - 1) * 100 - FEE_PCT
                    stats.trades.append(Trade(
                        symbol=symbol,
                        entry_time=open_pos["entry_time"],
                        exit_time=candle.time,
                        entry_price=open_pos["entry"],
                        exit_price=float(exit_price),
                        return_pct=ret,
                        exit_reason=reason,
                        duration=idx - open_pos["entry_idx"],
                    ))
                    open_pos = None

            # ---- چک ورود ----
            if open_pos is not None:
                continue

            # ML prob
            ml_prob = None
            if model is not None:
                row = X_all.iloc[idx]
                ml_prob = predict_prob_fast(model, row)

            # Rule
            rule = detect_bottom(candles, idx=idx)

            # تصمیم ورود
            if not entry_checker(ml_prob, rule):
                continue

            entry_price = float(candle.close)
            tp = entry_price * (1 + TP_PCT / 100)
            sl = entry_price * (1 - SL_PCT / 100)

            open_pos = {
                "entry": entry_price,
                "tp": tp,
                "sl": sl,
                "entry_idx": idx,
                "entry_time": candle.time,
            }

    return stats


def print_stats(s: BacktestStats):
    print(f"\n{'='*70}")
    print(f"📊 {s.name}")
    print(f"{'='*70}")
    print(f"  تعداد ترید:    {s.total}")
    if s.total == 0:
        return
    print(f"  برد / باخت:    {s.wins} / {s.losses}")
    print(f"  Win Rate:      {s.win_rate:.1f}%")
    print(f"  میانگین سود:   {s.avg_win:+.3f}%")
    print(f"  میانگین ضرر:   {s.avg_loss:+.3f}%")
    print(f"  🔥 بازده کل:    {s.total_return:+.2f}%")


async def main():
    print(f"📥 دریافت {len(SYMBOLS)} نماد روی {TIMEFRAME}...\n")
    markets_data = await fetch_all()
    print(f"✅ {len(markets_data)} نماد دریافت شد\n")

    print("🧠 لود مدل ML...")
    try:
        model = load_model()
        print("✅ مدل لود شد\n")
    except FileNotFoundError:
        print("❌ مدل نیست! اول train کن")
        return

    # ---------- ۴ استراتژی ----------

    # ۱. فقط قوانین
    def only_rules(ml_prob, rule):
        return rule.is_bottom and rule.score >= RULE_MIN_SCORE

    # ۲. فقط ML
    def only_ml(ml_prob, rule):
        return ml_prob is not None and ml_prob >= ML_STRONG

    # ۳. ML + قوانین (هر دو)
    def ml_and_rules(ml_prob, rule):
        return (
            ml_prob is not None
            and ml_prob >= ML_STRONG
            and rule.is_bottom
            and rule.score >= RULE_MIN_SCORE - 1
        )

    # ۴. ML یا قوانین
    def ml_or_rules(ml_prob, rule):
        return (
            (ml_prob is not None and ml_prob >= ML_STRONG)
            or (rule.is_bottom and rule.score >= RULE_MIN_SCORE)
        )

    strategies = [
        ("① فقط قوانین", only_rules),
        ("② فقط ML", only_ml),
        ("③ ML + قوانین (AND)", ml_and_rules),
        ("④ ML یا قوانین (OR)", ml_or_rules),
    ]

    results = []
    for name, checker in strategies:
        stats = run_one_strategy(name, markets_data, model, checker)
        results.append(stats)
        print_stats(stats)

    # ---------- بهترین ----------
    valid = [s for s in results if s.total >= 5]
    if valid:
        best = max(valid, key=lambda s: s.total_return)
        print(f"\n{'='*70}")
        print(f"🏆 بهترین استراتژی: {best.name}")
        print(f"   بازده: {best.total_return:+.2f}%  |  ترید: {best.total}  |  WR: {best.win_rate:.1f}%")
        print(f"{'='*70}")


if __name__ == "__main__":
    asyncio.run(main())
