"""بهینه‌سازی Grid — تست ترکیب‌های مختلف روی 1h."""

import asyncio
import time
from itertools import product

from app.application.use_cases.get_candles import GetCandlesUseCase
from app.core.config import get_settings
from app.infrastructure.exchange.wallex.client import WallexExchange
from app.services.bots.grid_bot.strategy import _calc_adx
from app.services.indicators import atr

SYMBOLS = ["DOGETMN", "XRPTMN", "TRXTMN", "ADATMN", "GRAMTMN", "ZECTMN", "LINKTMN", "HBARTMN"]
TF = "1h"
INITIAL_CAPITAL = 300_000
FEE_PCT = 0.2
N_LEVELS = 3
TIMEOUT_CANDLES = 100


async def fetch_all():
    settings = get_settings()
    async def one(sym):
        ex = WallexExchange.create(settings)
        try:
            uc = GetCandlesUseCase(exchange=ex)
            return sym, await uc.execute(symbol=sym, timeframe=TF, limit=2000)
        except Exception:
            return sym, []
        finally:
            await ex.aclose()
    results = await asyncio.gather(*[one(s) for s in SYMBOLS])
    return {s: c for s, c in results if c}


def _last(v):
    for x in reversed(v):
        if x is not None:
            return x
    return None


def backtest(markets_data, cash_pct, spacing_mult, escape_pct, adx_max=25.0):
    n = len(markets_data)
    per_symbol = INITIAL_CAPITAL / n
    total_final = 0
    all_trades = []
    worst_dd = 0

    for symbol, candles in markets_data.items():
        cash = per_symbol
        holdings = 0.0
        avg_buy = 0.0
        peak = per_symbol
        max_dd = 0.0
        session = None

        for idx in range(50, len(candles)):
            price = float(candles[idx].close)
            window = candles[: idx + 1]

            equity = cash + holdings * price
            if equity > peak: peak = equity
            dd = (peak - equity) / peak * 100 if peak > 0 else 0
            if dd > max_dd: max_dd = dd

            if session is None:
                adx = _calc_adx(window, 14)
                if adx >= adx_max:
                    continue
                atr_vals = atr(window, 14)
                atr_v = _last(atr_vals)
                if atr_v is None or atr_v <= 0:
                    continue
                spacing = float(atr_v) * spacing_mult
                if spacing <= 0 or spacing > price * 0.1:
                    continue
                cap_per = cash * (cash_pct / 100)
                levels = []
                for i in range(1, N_LEVELS + 1):
                    bp = price - i * spacing
                    if bp <= 0: continue
                    levels.append({
                        "buy_price": bp,
                        "sell_price": bp + spacing,
                        "qty": cap_per / bp,
                        "state": "waiting",
                    })
                if len(levels) < N_LEVELS: continue
                session = {"levels": levels, "start_price": price,
                           "start_idx": idx, "spacing": spacing}
                continue

            if abs(price - session["start_price"]) / session["start_price"] * 100 > escape_pct:
                if holdings > 0:
                    rev = holdings * price
                    fee = rev * FEE_PCT / 100
                    cash += rev - fee
                    all_trades.append((rev - fee) - holdings * avg_buy)
                    holdings = 0
                    avg_buy = 0
                session = None
                continue

            if idx - session["start_idx"] > TIMEOUT_CANDLES:
                if holdings > 0:
                    rev = holdings * price
                    fee = rev * FEE_PCT / 100
                    cash += rev - fee
                    all_trades.append((rev - fee) - holdings * avg_buy)
                    holdings = 0
                    avg_buy = 0
                session = None
                continue

            for lvl in session["levels"]:
                if lvl["state"] == "waiting" and price <= lvl["buy_price"]:
                    cost = lvl["qty"] * price
                    fee = cost * FEE_PCT / 100
                    if cost + fee <= cash:
                        cash -= cost + fee
                        if holdings > 0:
                            old = avg_buy * holdings
                            holdings += lvl["qty"]
                            avg_buy = (old + cost) / holdings
                        else:
                            holdings = lvl["qty"]
                            avg_buy = price
                        lvl["state"] = "holding"
                elif lvl["state"] == "holding" and price >= lvl["sell_price"]:
                    qty = min(lvl["qty"], holdings)
                    if qty <= 0: continue
                    rev = qty * price
                    fee = rev * FEE_PCT / 100
                    cash += rev - fee
                    all_trades.append((rev - fee) - qty * avg_buy)
                    holdings -= qty
                    if holdings <= 1e-12:
                        holdings = 0
                        avg_buy = 0
                    lvl["state"] = "waiting"

        if holdings > 0:
            price = float(candles[-1].close)
            rev = holdings * price
            fee = rev * FEE_PCT / 100
            cash += rev - fee
            all_trades.append((rev - fee) - holdings * avg_buy)

        total_final += cash
        worst_dd = max(worst_dd, max_dd)

    wins = sum(1 for t in all_trades if t > 0)
    wr = wins / len(all_trades) * 100 if all_trades else 0
    ret = (total_final / INITIAL_CAPITAL - 1) * 100

    return {
        "return": ret,
        "trades": len(all_trades),
        "wr": wr,
        "dd": worst_dd,
    }


async def main():
    print("📥 دریافت داده 1h...")
    data = await fetch_all()
    print(f"✅ {len(data)} نماد، {sum(len(c) for c in data.values())} کندل\n")

    combos = list(product(
        [25.0, 30.0, 35.0, 40.0, 50.0],  # cash_pct
        [0.3, 0.4, 0.5, 0.6, 0.8],       # spacing_mult
        [4.0, 5.0, 6.0],                 # escape_pct
    ))
    print(f"🎯 {len(combos)} ترکیب\n")

    print(f"{'cash%':>6} {'spacing':>8} {'esc%':>5} {'بازده':>9} {'ترید':>6} {'WR':>6} {'DD':>6} {'R/DD':>6}")
    print("─" * 70)

    results = []
    start = time.time()
    for cash_pct, spacing, esc in combos:
        r = backtest(data, cash_pct, spacing, esc)
        rdd = r["return"] / r["dd"] if r["dd"] > 0 else 0
        results.append({**r, "cash": cash_pct, "spacing": spacing, "esc": esc})
        print(f"{cash_pct:>6.0f} {spacing:>8.1f} {esc:>5.0f} {r['return']:>+8.2f}% {r['trades']:>6} {r['wr']:>5.1f}% {r['dd']:>5.2f}% {rdd:>6.2f}")

    print(f"\n⏱️  {time.time()-start:.1f}s")

    # بهترین‌ها
    print(f"\n{'='*70}")
    best_ret = max(results, key=lambda x: x["return"])
    print(f"🏆 بهترین بازده: cash={best_ret['cash']:.0f}% spacing={best_ret['spacing']} esc={best_ret['esc']:.0f}%")
    print(f"   بازده: {best_ret['return']:+.2f}%  |  DD: {best_ret['dd']:.2f}%  |  WR: {best_ret['wr']:.1f}%  |  ترید: {best_ret['trades']}")

    best_rdd = max(results, key=lambda x: x["return"]/x["dd"] if x["dd"] > 0 else 0)
    print(f"\n🏆 بهترین بازده/DD:")
    print(f"   cash={best_rdd['cash']:.0f}% spacing={best_rdd['spacing']} esc={best_rdd['esc']:.0f}%")
    print(f"   بازده: {best_rdd['return']:+.2f}%  |  DD: {best_rdd['dd']:.2f}%  |  نسبت: {best_rdd['return']/best_rdd['dd']:.2f}")


if __name__ == "__main__":
    asyncio.run(main())
