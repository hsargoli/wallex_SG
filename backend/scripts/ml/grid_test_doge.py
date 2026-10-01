"""Grid test فقط روی ارزهای ارزون."""

import asyncio

from app.application.use_cases.get_candles import GetCandlesUseCase
from app.core.config import get_settings
from app.infrastructure.exchange.wallex.client import WallexExchange
from app.services.bots.grid_bot.strategy import _calc_adx
from app.services.indicators import atr

# فقط ارزهای ارزون که قیمتشون ~1000-100,000 ریال
SYMBOLS = ["DOGETMN", "XRPTMN", "TRXTMN", "ADATMN", "GRAMTMN"]
INITIAL_CAPITAL = 300_000
FEE_PCT = 0.2
ADX_MAX = 25.0
SPACING_ATR = 1.0
N_LEVELS = 3
CASH_PER_LEVEL_PCT = 15.0
ESCAPE_PCT = 5.0
TIMEOUT_CANDLES = 100


async def fetch_all(tf):
    settings = get_settings()
    async def one(sym):
        ex = WallexExchange.create(settings)
        try:
            uc = GetCandlesUseCase(exchange=ex)
            return sym, await uc.execute(symbol=sym, timeframe=tf, limit=2000)
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


def backtest_symbol(symbol, candles, initial_cash):
    cash = initial_cash
    holdings = 0.0
    avg_buy = 0.0
    trades = []
    peak = initial_cash
    max_dd = 0.0
    sessions = 0
    session = None

    for idx in range(50, len(candles)):
        price = float(candles[idx].close)
        window = candles[:idx+1]

        equity = cash + holdings * price
        if equity > peak: peak = equity
        dd = (peak - equity) / peak * 100 if peak > 0 else 0
        if dd > max_dd: max_dd = dd

        if session is None:
            adx = _calc_adx(window, 14)
            if adx >= ADX_MAX:
                continue
            atr_vals = atr(window, 14)
            atr_v = _last(atr_vals)
            if atr_v is None or atr_v <= 0:
                continue
            spacing = float(atr_v) * SPACING_ATR
            if spacing <= 0:
                continue
            cap_per = cash * (CASH_PER_LEVEL_PCT / 100)
            levels = []
            for i in range(1, N_LEVELS + 1):
                buy_p = price - i * spacing
                if buy_p <= 0: continue
                qty = cap_per / buy_p
                levels.append({
                    "buy_price": buy_p,
                    "sell_price": buy_p + spacing,
                    "qty": qty,
                    "state": "waiting",
                })
            if not levels: continue
            session = {"levels": levels, "start_price": price,
                       "start_idx": idx, "spacing": spacing}
            sessions += 1
            continue

        # escape
        if abs(price - session["start_price"]) / session["start_price"] * 100 > ESCAPE_PCT:
            if holdings > 0:
                revenue = holdings * price
                fee = revenue * FEE_PCT / 100
                cash += revenue - fee
                pnl = (revenue - fee) - holdings * avg_buy
                trades.append(pnl)
                holdings = 0
                avg_buy = 0
            session = None
            continue

        if idx - session["start_idx"] > TIMEOUT_CANDLES:
            if holdings > 0:
                revenue = holdings * price
                fee = revenue * FEE_PCT / 100
                cash += revenue - fee
                pnl = (revenue - fee) - holdings * avg_buy
                trades.append(pnl)
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
                revenue = qty * price
                fee = revenue * FEE_PCT / 100
                cash += revenue - fee
                pnl = (revenue - fee) - qty * avg_buy
                trades.append(pnl)
                holdings -= qty
                if holdings <= 1e-12:
                    holdings = 0
                    avg_buy = 0
                lvl["state"] = "waiting"

    if holdings > 0:
        price = float(candles[-1].close)
        revenue = holdings * price
        fee = revenue * FEE_PCT / 100
        cash += revenue - fee
        pnl = (revenue - fee) - holdings * avg_buy
        trades.append(pnl)

    return {
        "symbol": symbol,
        "initial": initial_cash,
        "final": cash,
        "trades": trades,
        "max_dd": max_dd,
        "sessions": sessions,
    }


async def main():
    for tf in ["15m", "1h", "4h"]:
        data = await fetch_all(tf)
        if not data: continue
        n = len(data)
        per = INITIAL_CAPITAL / n

        print(f"\n{'='*70}")
        print(f"🎯 TF={tf}  ({n} نماد × {per:,.0f})")
        print(f"{'='*70}")

        # چک قیمت‌ها
        for sym, candles in data.items():
            price = float(candles[-1].close)
            print(f"  {sym:10} price={price:>15,.0f}")

        all_trades = []
        total_final = 0
        worst_dd = 0

        for sym, candles in data.items():
            r = backtest_symbol(sym, candles, per)
            total_final += r["final"]
            all_trades.extend(r["trades"])
            worst_dd = max(worst_dd, r["max_dd"])
            print(f"  → {sym:10} بازده: {(r['final']/r['initial']-1)*100:>+8.2f}%  |  "
                  f"ترید: {len(r['trades']):>3}  |  DD: {r['max_dd']:>5.1f}%")

        wins = sum(1 for t in all_trades if t > 0)
        losses = sum(1 for t in all_trades if t <= 0)
        wr = wins / len(all_trades) * 100 if all_trades else 0
        ret = (total_final / INITIAL_CAPITAL - 1) * 100

        print(f"\n  {'─'*50}")
        print(f"  🎯 کل: بازده {ret:+.2f}%  |  ترید {len(all_trades)}  |  WR {wr:.1f}%  |  DD {worst_dd:.1f}%")


if __name__ == "__main__":
    asyncio.run(main())
