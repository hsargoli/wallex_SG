"""Backtest ربات کامل (Trading Brain)."""

import asyncio
from dataclasses import dataclass, field

from app.application.use_cases.get_candles import GetCandlesUseCase
from app.core.config import get_settings
from app.infrastructure.exchange.wallex.client import WallexExchange
from app.services.trading_brain import make_decision

SYMBOLS = ["BTCTMN", "ETHTMN", "XRPTMN", "DOGETMN", "SOLTMN"]
TF = "15m"
N_CANDLES = 2000
WARMUP = 150
MAX_DURATION = 24
FEE_PCT = 0.2


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
    trades: list = field(default_factory=list)
    initial: float = 300_000.0
    capital: float = 300_000.0
    peak: float = 300_000.0
    max_dd: float = 0.0

    @property
    def total(self): return len(self.trades)
    @property
    def wins(self): return sum(1 for t in self.trades if t > 0)
    @property
    def losses(self): return sum(1 for t in self.trades if t <= 0)
    @property
    def wr(self): return (self.wins / self.total * 100) if self.total else 0
    @property
    def total_return(self): return (self.capital - self.initial) / self.initial * 100


def run_backtest(markets_data):
    stats = Stats()
    max_positions = 2

    for symbol, candles in markets_data.items():
        open_pos = None

        for idx in range(WARMUP, len(candles)):
            candle = candles[idx]

            # ---- چک خروج ----
            if open_pos is not None:
                exit_price = None
                if candle.high >= open_pos["tp"]:
                    exit_price = open_pos["tp"]
                elif candle.low <= open_pos["sl"]:
                    exit_price = open_pos["sl"]
                elif idx - open_pos["entry_idx"] >= MAX_DURATION:
                    exit_price = float(candle.close)

                if exit_price is not None:
                    pnl_pct = (float(exit_price) / open_pos["entry"] - 1) * 100 - FEE_PCT
                    # محاسبه‌ی سود بر اساس اندازه‌ی پوزیشن
                    trade_pnl = (pnl_pct / 100) * open_pos["invest"]
                    stats.capital += trade_pnl
                    if stats.capital > stats.peak:
                        stats.peak = stats.capital
                    dd = (stats.peak - stats.capital) / stats.peak * 100
                    if dd > stats.max_dd:
                        stats.max_dd = dd
                    stats.trades.append(pnl_pct)
                    open_pos = None

            if open_pos is not None:
                continue

            # ---- چک ورود ----
            window = candles[:idx + 1]
            decision = make_decision(window)

            if not decision.should_trade:
                continue

            # اندازه‌ی پوزیشن
            invest = stats.initial * (decision.position_size_pct / 100)
            invest = min(invest, stats.capital * 0.95)
            if invest < 10_000:
                continue

            entry = float(candle.close)
            open_pos = {
                "entry": entry,
                "invest": invest,
                "tp": entry * (1 + decision.take_profit_pct / 100),
                "sl": entry * (1 - decision.stop_loss_pct / 100),
                "entry_idx": idx,
            }

    return stats


async def main():
    print(f"📥 دریافت {len(SYMBOLS)} نماد × {TF}...\n")
    markets_data = await fetch_all()
    print(f"✅ {len(markets_data)} نماد\n")

    print("🧠 Backtest با Trading Brain...")
    stats = run_backtest(markets_data)

    print(f"\n{'='*60}")
    print(f"📊 نتایج Trading Brain Backtest:")
    print(f"{'='*60}")
    print(f"  سرمایه اولیه:  {stats.initial:>12,.0f} تومان")
    print(f"  سرمایه نهایی:  {stats.capital:>12,.0f} تومان")
    print(f"  بازده کل:      {stats.total_return:>+11.2f}%")
    print(f"  Max Drawdown:  {stats.max_dd:>11.2f}%")
    print(f"  تعداد ترید:    {stats.total:>12}")
    print(f"  برد / باخت:    {stats.wins:>5} / {stats.losses}")
    print(f"  Win Rate:      {stats.wr:>11.1f}%")
    if stats.trades:
        avg_w = sum(t for t in stats.trades if t > 0) / max(1, stats.wins)
        avg_l = sum(t for t in stats.trades if t <= 0) / max(1, stats.losses)
        print(f"  میانگین سود:   {avg_w:>+11.3f}%")
        print(f"  میانگین ضرر:   {avg_l:>+11.3f}%")


if __name__ == "__main__":
    asyncio.run(main())
