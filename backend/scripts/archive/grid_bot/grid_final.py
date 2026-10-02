"""Grid Final — مقایسه ۳ حالت بهینه."""

import asyncio

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


def backtest(data, cash_pct, spacing_mult, escape_pct,
             use_max_exposure=False, max_exposure=40.0,
             use_regime_filter=False, adx_max=25.0):
    n = len(data)
    per = INITIAL_CAPITAL / n
    total_final = 0
    all_trades = []
    worst_dd = 0
    total_skip = 0
    sessions_total = 0

    for symbol, candles in data.items():
        cash = per
        holdings = 0.0
        avg_buy = 0.0
        peak = per
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
                if use_regime_filter and adx >= adx_max:
                    total_skip += 1
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
                sessions_total += 1
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

            if idx - session["start_idx"] > 100:
                if holdings > 0:
                    rev = holdings * price
                    fee = rev * FEE_PCT / 100
                    cash += rev - fee
                    all_trades.append((rev - fee) - holdings * avg_buy)
                    holdings = 0
                    avg_buy = 0
                session = None
                continue

            exposure_pct = (holdings * price) / equity * 100 if equity > 0 else 0
            can_buy = True
            if use_max_exposure and exposure_pct >= max_exposure:
                can_buy = False

            for lvl in session["levels"]:
                if lvl["state"] == "waiting" and price <= lvl["buy_price"]:
                    if not can_buy:
                        continue
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
                        equity = cash + holdings * price
                        exposure_pct = (holdings * price) / equity * 100 if equity > 0 else 0
                        if use_max_exposure and exposure_pct >= max_exposure:
                            can_buy = False

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
    rdd = ret / worst_dd if worst_dd > 0 else 0

    return {
        "return": ret, "trades": len(all_trades), "wr": wr,
        "dd": worst_dd, "rdd": rdd, "skip": total_skip,
        "sessions": sessions_total,
    }


async def main():
    data = await fetch_all()
    print(f"✅ {len(data)} نماد\n")

    configs = [
        ("محافظه‌کار (10%/1.0/5%)", 10.0, 1.0, 5.0, False, 40.0, False),
        ("متعادل (25%/0.6/5%)", 25.0, 0.6, 5.0, False, 40.0, False),
        ("تهاجمی (30%/0.3/5%)", 30.0, 0.3, 5.0, False, 40.0, False),
        ("بهینه + Max Exposure", 30.0, 0.3, 5.0, True, 40.0, False),
        ("بهینه + Regime Filter", 30.0, 0.3, 5.0, False, 40.0, True),
        ("بهینه + هر دو", 30.0, 0.3, 5.0, True, 40.0, True),
    ]

    print(f"{'config':<35} {'بازده':>9} {'ترید':>5} {'WR':>6} {'DD':>7} {'R/DD':>6} {'sessions':>8}")
    print("─" * 90)
    for name, cash, sp, esc, me, mem, rf in configs:
        r = backtest(data, cash, sp, esc, me, mem, rf)
        print(f"{name:<35} {r['return']:>+8.2f}% {r['trades']:>5} {r['wr']:>5.1f}% {r['dd']:>6.2f}% {r['rdd']:>6.2f} {r['sessions']:>8}")


if __name__ == "__main__":
    asyncio.run(main())
