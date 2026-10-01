"""Backtest ربات ساده."""

import asyncio
from dataclasses import dataclass, field

from app.application.use_cases.get_candles import GetCandlesUseCase
from app.core.config import get_settings
from app.infrastructure.exchange.wallex.client import WallexExchange
from app.services.simple_bot import (
    FEE_PCT, MAX_POSITIONS, POSITION_SIZE_PCT,
    check_simple_exit, make_simple_decision,
)

SYMBOLS = ["BTCTMN", "ETHTMN", "XRPTMN", "DOGETMN", "SOLTMN"]
TF = "15m"
N_CANDLES = 2000
WARMUP = 100
INITIAL_CAPITAL = 300_000


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


def run_backtest(markets_data):
    capital = INITIAL_CAPITAL
    peak = capital
    max_dd = 0.0
    trades = []

    # جمع همه کندل‌ها بر اساس زمان
    events = []
    for symbol, candles in markets_data.items():
        for i, c in enumerate(candles):
            events.append((c.time, symbol, i, c))
    events.sort(key=lambda x: x[0])

    open_positions: dict[str, dict] = {}

    for event_time, symbol, idx, candle in events:
        # چک خروج
        if symbol in open_positions:
            pos = open_positions[symbol]
            should_exit, exit_price, reason = check_simple_exit(
                pos["entry"], pos["tp"], pos["sl"],
                candle, idx - pos["entry_idx"],
            )
            if should_exit:
                pnl_pct = (exit_price / pos["entry"] - 1) * 100 - FEE_PCT
                pnl_tmn = pos["invest"] * pnl_pct / 100
                capital += pnl_tmn
                if capital > peak:
                    peak = capital
                dd = (peak - capital) / peak * 100
                if dd > max_dd:
                    max_dd = dd
                trades.append(pnl_pct)
                del open_positions[symbol]

        # چک ورود
        if len(open_positions) >= MAX_POSITIONS:
            continue
        if symbol in open_positions:
            continue

        window = markets_data[symbol][: idx + 1]
        if len(window) < WARMUP:
            continue

        decision = make_simple_decision(window)
        if not decision.should_trade:
            continue

        invest = capital * (POSITION_SIZE_PCT / 100)
        invest = min(invest, capital * 0.95)
        if invest < 10_000:
            continue

        open_positions[symbol] = {
            "entry": decision.entry_price,
            "tp": decision.take_profit,
            "sl": decision.stop_loss,
            "invest": invest,
            "entry_idx": idx,
        }

    return capital, max_dd, trades


async def main():
    print(f"📥 دریافت {len(SYMBOLS)} نماد × {TF}...\n")
    markets_data = await fetch_all()
    print(f"✅ {len(markets_data)} نماد\n")

    capital, max_dd, trades = run_backtest(markets_data)

    wins = sum(1 for t in trades if t > 0)
    losses = sum(1 for t in trades if t <= 0)
    total = len(trades)

    print(f"{'='*60}")
    print(f"📊 Simple Bot Backtest:")
    print(f"{'='*60}")
    print(f"  سرمایه اولیه:  {INITIAL_CAPITAL:>12,.0f}")
    print(f"  سرمایه نهایی:  {capital:>12,.0f}")
    print(f"  سود/زیان:      {capital - INITIAL_CAPITAL:>+12,.0f} تومان")
    print(f"  بازده کل:      {(capital/INITIAL_CAPITAL - 1)*100:>+11.2f}%")
    print(f"  Max Drawdown:  {max_dd:>11.2f}%")
    print(f"  تعداد ترید:    {total:>12}")
    print(f"  برد/باخت:      {wins:>5} / {losses}")
    if total > 0:
        print(f"  Win Rate:      {wins/total*100:>11.1f}%")
    if wins > 0:
        print(f"  میانگین سود:   {sum(t for t in trades if t > 0)/wins:>+11.3f}%")
    if losses > 0:
        print(f"  میانگین ضرر:   {sum(t for t in trades if t <= 0)/losses:>+11.3f}%")


if __name__ == "__main__":
    asyncio.run(main())
