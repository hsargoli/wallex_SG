"""Backtest نوسان‌گیر روی نمادهای نوسان‌دار."""

import asyncio

from app.application.use_cases.get_candles import GetCandlesUseCase
from app.core.config import get_settings
from app.infrastructure.exchange.wallex.client import WallexExchange
from app.services.bots.volatility_hunter.config import VolatilityHunterConfig
from app.services.bots.volatility_hunter.strategy import evaluate_entry, evaluate_exit

SYMBOLS = ["ZECTMN", "DASHTMN", "GRAMTMN", "XRPTMN", "DOGETMN"]
TF = "1h"
N_CANDLES = 2000
INITIAL_CAPITAL = 300_000
FEE_PCT = 0.2
MAX_POSITIONS = 2


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


def run_backtest(markets_data, config):
    capital = INITIAL_CAPITAL
    peak = capital
    max_dd = 0
    trades = []
    open_positions = {}

    events = []
    for sym, candles in markets_data.items():
        for i, c in enumerate(candles):
            events.append((c.time, sym, i, c))
    events.sort(key=lambda x: x[0])

    for _, sym, idx, candle in events:
        # Exit
        if sym in open_positions:
            pos = open_positions[sym]
            window = markets_data[sym][: idx + 1]
            should_exit, exit_p, reason = evaluate_exit(
                window, pos["entry"], pos["sl"], pos["tp"], config,
            )
            if should_exit:
                pnl = (exit_p / pos["entry"] - 1) * 100 - FEE_PCT
                capital += pos["invest"] * pnl / 100
                if capital > peak: peak = capital
                dd = (peak - capital) / peak * 100
                if dd > max_dd: max_dd = dd
                trades.append({"pnl": pnl, "reason": reason, "symbol": sym})
                del open_positions[sym]

        # Entry
        if len(open_positions) >= MAX_POSITIONS:
            continue
        if sym in open_positions:
            continue
        if idx < config.warmup_candles:
            continue

        window = markets_data[sym][: idx + 1]
        sig = evaluate_entry(window, config)
        if sig is None: continue

        invest = capital * (config.position_size_pct / 100)
        if invest < 5000: continue

        open_positions[sym] = {
            "entry": sig.entry_price,
            "sl": sig.stop_loss,
            "tp": sig.take_profit,
            "invest": invest,
        }

    # بستن بازها
    for sym, pos in open_positions.items():
        last = markets_data[sym][-1]
        pnl = (float(last.close) / pos["entry"] - 1) * 100 - FEE_PCT
        capital += pos["invest"] * pnl / 100
        trades.append({"pnl": pnl, "reason": "end", "symbol": sym})

    wins = sum(1 for t in trades if t["pnl"] > 0)
    wr = wins / len(trades) * 100 if trades else 0
    ret = (capital / INITIAL_CAPITAL - 1) * 100
    rdd = ret / max_dd if max_dd > 0 else 0

    return {
        "return": ret, "trades": len(trades), "wins": wins,
        "losses": len(trades) - wins, "wr": wr, "dd": max_dd, "rdd": rdd,
        "trade_list": trades,
    }


async def main():
    print(f"📥 دریافت {len(SYMBOLS)} نماد ({TF})...\n")
    data = await fetch_all()
    print(f"✅ {len(data)} نماد\n")

    config = VolatilityHunterConfig()
    result = run_backtest(data, config)

    print(f"{'='*60}")
    print(f"📊 Volatility Hunter Backtest")
    print(f"{'='*60}")
    print(f"  بازده:        {result['return']:>+9.2f}%")
    print(f"  ترید:         {result['trades']}")
    print(f"  برد/باخت:     {result['wins']} / {result['losses']}")
    print(f"  WR:           {result['wr']:>8.1f}%")
    print(f"  Max DD:       {result['dd']:>8.2f}%")
    print(f"  R/DD:         {result['rdd']:>8.2f}")

    # per-symbol breakdown
    print(f"\n  per-symbol:")
    for sym in SYMBOLS:
        sym_trades = [t for t in result["trade_list"] if t["symbol"] == sym]
        if sym_trades:
            w = sum(1 for t in sym_trades if t["pnl"] > 0)
            print(f"    {sym:10} {len(sym_trades):>3} ترید  WR={w/len(sym_trades)*100:>5.1f}%")


if __name__ == "__main__":
    asyncio.run(main())
