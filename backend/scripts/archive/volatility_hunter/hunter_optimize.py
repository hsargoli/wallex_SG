"""بهینه‌سازی Volatility Hunter."""

import asyncio
import time
from itertools import product

from app.application.use_cases.get_candles import GetCandlesUseCase
from app.core.config import get_settings
from app.infrastructure.exchange.wallex.client import WallexExchange
from app.services.bots.volatility_hunter.config import VolatilityHunterConfig
from app.services.bots.volatility_hunter.strategy import evaluate_entry, evaluate_exit

SYMBOLS = ["ZECTMN", "DASHTMN", "GRAMTMN", "XRPTMN", "DOGETMN", "LINKTMN"]
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


def backtest(markets_data, min_atr_pct, min_range_pct, buy_zone_pct,
             sl_pct=3.0, tp_pct=5.0):
    config = VolatilityHunterConfig()
    config.min_atr_pct = min_atr_pct
    config.min_range_pct = min_range_pct
    config.buy_zone_pct = buy_zone_pct
    config.stop_loss_pct = sl_pct
    config.take_profit_pct = tp_pct

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

        if len(open_positions) >= MAX_POSITIONS or sym in open_positions:
            continue
        if idx < 100:
            continue

        window = markets_data[sym][: idx + 1]
        sig = evaluate_entry(window, config)
        if sig is None: continue

        invest = capital * (config.position_size_pct / 100)
        if invest < 5000: continue

        open_positions[sym] = {
            "entry": sig.entry_price, "sl": sig.stop_loss,
            "tp": sig.take_profit, "invest": invest,
        }

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
        "return": ret, "trades": len(trades), "wr": wr,
        "dd": max_dd, "rdd": rdd,
    }


async def main():
    print("📥 دریافت داده...\n")
    data = await fetch_all()
    print(f"✅ {len(data)} نماد\n")

    combos = list(product(
        [1.0, 1.3, 1.5, 1.8],       # min_atr_pct
        [3.0, 5.0, 7.0, 10.0],       # min_range_pct
        [10.0, 15.0, 20.0, 25.0],    # buy_zone_pct
    ))

    print(f"🎯 {len(combos)} ترکیب\n")
    print(f"{'atr%':>5} {'range%':>7} {'zone%':>6} {'بازده':>9} {'ترید':>5} {'WR':>6} {'DD':>6} {'R/DD':>6}")
    print("─" * 75)

    results = []
    start = time.time()
    for atr, rng, zone in combos:
        r = backtest(data, atr, rng, zone)
        r.update({"atr": atr, "range": rng, "zone": zone})
        results.append(r)
        print(f"{atr:>5.1f} {rng:>7.1f} {zone:>6.0f} {r['return']:>+8.2f}% {r['trades']:>5} {r['wr']:>5.1f}% {r['dd']:>5.2f}% {r['rdd']:>6.2f}")

    print(f"\n⏱️  {time.time()-start:.1f}s")

    # بهترین بر اساس R/DD (با حداقل 15 ترید)
    valid = [r for r in results if r["trades"] >= 15]
    if valid:
        best = max(valid, key=lambda x: x["rdd"])
        print(f"\n🏆 بهترین R/DD (>=15 ترید):")
        print(f"   atr={best['atr']}% range={best['range']}% zone={best['zone']}%")
        print(f"   بازده: {best['return']:+.2f}%  DD: {best['dd']:.2f}%  R/DD: {best['rdd']:.2f}")
        print(f"   ترید: {best['trades']}  WR: {best['wr']:.1f}%")

    # بهترین بر اساس بازده
    best_ret = max(results, key=lambda x: x["return"])
    print(f"\n🏆 بهترین بازده:")
    print(f"   atr={best_ret['atr']}% range={best_ret['range']}% zone={best_ret['zone']}%")
    print(f"   بازده: {best_ret['return']:+.2f}%  DD: {best_ret['dd']:.2f}%  R/DD: {best_ret['rdd']:.2f}")
    print(f"   ترید: {best_ret['trades']}  WR: {best_ret['wr']:.1f}%")


if __name__ == "__main__":
    asyncio.run(main())
