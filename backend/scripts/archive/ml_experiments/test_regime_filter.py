"""تست استراتژی با فیلتر Regime.

مقایسه:
  A) استراتژی قوانین (بدون فیلتر)
  B) استراتژی + فقط رژیم‌های tradeable
"""

import asyncio
from dataclasses import dataclass, field

from app.application.use_cases.get_candles import GetCandlesUseCase
from app.core.config import get_settings
from app.infrastructure.exchange.wallex.client import WallexExchange
from app.services.bottom_detector import detect_bottom
from app.services.ml_bottom_model import build_features, candles_to_df, load_model
from app.services.regime_detector import detect_regime

SYMBOLS = ["BTCTMN", "ETHTMN", "XRPTMN", "DOGETMN", "SOLTMN"]
TF = "15m"
N_CANDLES = 2000
WARMUP = 100
LOOKAHEAD = 24
TP_PCT = 2.0
SL_PCT = 1.5
FEE_PCT = 0.2
MAX_DURATION = 24

RULE_MIN_SCORE = 5
ML_STRONG = 0.55


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


@dataclass
class Stats:
    name: str
    trades: list = field(default_factory=list)
    @property
    def total(self): return len(self.trades)
    @property
    def wins(self): return sum(1 for t in self.trades if t > 0)
    @property
    def losses(self): return sum(1 for t in self.trades if t <= 0)
    @property
    def wr(self): return (self.wins / self.total * 100) if self.total else 0
    @property
    def total_return(self):
        if not self.trades: return 0
        eq = 1.0
        for r in self.trades:
            eq *= (1 + r / 100)
        return (eq - 1) * 100


def run_backtest(markets_data, model, use_regime_filter: bool):
    stats = Stats(name="with_filter" if use_regime_filter else "no_filter")

    for symbol, candles in markets_data.items():
        df = candles_to_df(candles)
        X_all = build_features(df)

        # Batch ML predict
        ml_probs = [None] * len(X_all)
        valid_mask = ~X_all.isna().any(axis=1)
        if valid_mask.sum() > 0:
            probs = model.predict_proba(X_all[valid_mask])[:, 1]
            for i, idx in enumerate(X_all[valid_mask].index):
                ml_probs[idx] = float(probs[i])

        open_pos = None

        for idx in range(WARMUP, len(candles)):
            candle = candles[idx]

            # چک خروج
            if open_pos is not None:
                exit_price = None
                if candle.high >= open_pos["tp"]:
                    exit_price = open_pos["tp"]
                elif candle.low <= open_pos["sl"]:
                    exit_price = open_pos["sl"]
                elif idx - open_pos["entry_idx"] >= MAX_DURATION:
                    exit_price = float(candle.close)

                if exit_price is not None:
                    ret = (float(exit_price) / open_pos["entry"] - 1) * 100 - FEE_PCT
                    stats.trades.append(ret)
                    open_pos = None

            if open_pos is not None:
                continue

            # فیلتر Regime (فقط وقتی سیگنال ورود داریم)
            # اول چک کن آیا سیگنال هست یا نه
            ml_prob = ml_probs[idx]
            rule = detect_bottom(candles, idx=idx)

            should_enter = (
                (ml_prob is not None and ml_prob >= ML_STRONG)
                or (rule.is_bottom and rule.score >= RULE_MIN_SCORE)
            )
            if not should_enter:
                continue

            # حالا اگه فیلتر فعاله، regime رو چک کن
            if use_regime_filter:
                recent_candles = candles[:idx + 1][-200:]
                regime = detect_regime(recent_candles)
                if not regime.is_tradeable:
                    continue

            entry = float(candle.close)
            open_pos = {
                "entry": entry,
                "tp": entry * (1 + TP_PCT / 100),
                "sl": entry * (1 - SL_PCT / 100),
                "entry_idx": idx,
            }

    return stats


def print_stats(s: Stats):
    print(f"\n  {'بدون فیلتر Regime' if s.name == 'no_filter' else 'با فیلتر Regime'}")
    print(f"  {'─'*50}")
    print(f"    تریدها:      {s.total}")
    print(f"    برد/باخت:    {s.wins}/{s.losses}")
    print(f"    Win Rate:    {s.wr:.1f}%")
    print(f"    بازده کل:    {s.total_return:+.2f}%")


async def main():
    print(f"📥 دریافت {len(SYMBOLS)} نماد × {TF}...\n")
    markets_data = await fetch_all()
    print(f"✅ {len(markets_data)} نماد\n")

    print("🧠 لود مدل...")
    try:
        model = load_model()
        print("✅ لود شد\n")
    except Exception as e:
        print(f"❌ {e}")
        return

    # بدون فیلتر
    s_no = run_backtest(markets_data, model, use_regime_filter=False)
    # با فیلتر
    s_yes = run_backtest(markets_data, model, use_regime_filter=True)

    print(f"{'='*70}")
    print("📊 مقایسه:")
    print(f"{'='*70}")
    print_stats(s_no)
    print_stats(s_yes)

    print(f"\n{'='*70}")
    print("🎯 نتیجه:")
    print(f"{'='*70}")
    if s_no.total > 0 and s_yes.total > 0:
        diff = s_yes.total_return - s_no.total_return
        wr_diff = s_yes.wr - s_no.wr
        print(f"  تفاوت بازده:      {diff:+.2f}%")
        print(f"  تفاوت Win Rate:   {wr_diff:+.1f}%")
        if diff > 0:
            print("  ✅ فیلتر Regime کمک کرد!")
        elif diff < 0:
            print("  ⚠️ فیلتر Regime ضرر زد")
        else:
            print("  ⚪ تفاوت نداشت")


if __name__ == "__main__":
    asyncio.run(main())
