"""Grid Backtest — نسخه نهایی (per-symbol، بدون state مشترک).

قواعد:
  ۱. هر نماد مستقل
  ۲. capital بین نمادها تقسیم میشه
  ۳. هر سطح: یک خرید، یک فروش
  ۴. فقط در رنج فعال
  ۵. escape: فروش همه
"""

import asyncio
from dataclasses import dataclass

from app.application.use_cases.get_candles import GetCandlesUseCase
from app.core.config import get_settings
from app.infrastructure.exchange.wallex.client import WallexExchange
from app.services.bots.grid_bot.strategy import _calc_adx
from app.services.indicators import atr

SYMBOLS = ["BTCTMN", "ETHTMN", "XRPTMN", "SOLTMN", "BNBTMN",
           "ADATMN", "LINKTMN", "HBARTMN", "DASHTMN", "TRXTMN"]
INITIAL_CAPITAL = 300_000
FEE_PCT = 0.2  # 0.2% = 0.002 decimal
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


@dataclass
class SymbolResult:
    symbol: str
    initial: float
    final: float
    trades: list
    max_dd: float
    sessions: int
    escapes: int


def backtest_symbol(symbol: str, candles: list, initial_cash: float) -> SymbolResult:
    """بک‌تست یک نماد به‌صورت مستقل."""
    cash = initial_cash
    holdings = 0.0
    avg_buy = 0.0
    trades = []
    peak_equity = initial_cash
    max_dd = 0.0
    sessions = 0
    escapes = 0

    session = None  # dict

    for idx in range(50, len(candles)):
        price = float(candles[idx].close)
        window = candles[: idx + 1]

        # محاسبه equity
        equity = cash + holdings * price
        if equity > peak_equity:
            peak_equity = equity
        dd = (peak_equity - equity) / peak_equity * 100 if peak_equity > 0 else 0
        if dd > max_dd:
            max_dd = dd

        # ---------- شروع session جدید ----------
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
                if buy_p <= 0:
                    continue
                qty = cap_per / buy_p
                levels.append({
                    "buy_price": buy_p,
                    "sell_price": buy_p + spacing,
                    "qty": qty,
                    "state": "waiting",  # waiting | holding
                })

            if not levels:
                continue

            session = {
                "levels": levels,
                "start_price": price,
                "start_idx": idx,
                "spacing": spacing,
            }
            sessions += 1
            continue

        # ---------- Escape ----------
        diff_pct = abs(price - session["start_price"]) / session["start_price"] * 100
        if diff_pct > ESCAPE_PCT:
            if holdings > 0:
                revenue = holdings * price
                fee = revenue * FEE_PCT / 100
                cost = holdings * avg_buy
                pnl = (revenue - fee) - cost
                cash += revenue - fee
                trades.append(pnl)
                holdings = 0
                avg_buy = 0
            session = None
            escapes += 1
            continue

        # ---------- Timeout ----------
        if idx - session["start_idx"] > TIMEOUT_CANDLES:
            if holdings > 0:
                revenue = holdings * price
                fee = revenue * FEE_PCT / 100
                cost = holdings * avg_buy
                pnl = (revenue - fee) - cost
                cash += revenue - fee
                trades.append(pnl)
                holdings = 0
                avg_buy = 0
            session = None
            continue

        # ---------- پردازش سطوح ----------
        for lvl in session["levels"]:
            # خرید
            if lvl["state"] == "waiting" and price <= lvl["buy_price"]:
                cost = lvl["qty"] * price
                fee = cost * FEE_PCT / 100
                total = cost + fee
                if total <= cash:
                    cash -= total
                    # آپدیت holdings/avg
                    if holdings > 0:
                        old_cost = avg_buy * holdings
                        holdings += lvl["qty"]
                        avg_buy = (old_cost + cost) / holdings
                    else:
                        holdings = lvl["qty"]
                        avg_buy = price
                    lvl["state"] = "holding"

            # فروش
            elif lvl["state"] == "holding" and price >= lvl["sell_price"]:
                sell_qty = min(lvl["qty"], holdings)
                revenue = sell_qty * price
                fee = revenue * FEE_PCT / 100
                net = revenue - fee
                cost_basis = sell_qty * avg_buy
                pnl = net - cost_basis

                cash += net
                holdings -= sell_qty
                if holdings <= 0.000001:
                    holdings = 0
                    avg_buy = 0

                trades.append(pnl)
                lvl["state"] = "waiting"  # ریست برای cycle بعد

    # ---------- بستن نهایی ----------
    if holdings > 0:
        price = float(candles[-1].close)
        revenue = holdings * price
        fee = revenue * FEE_PCT / 100
        cost = holdings * avg_buy
        pnl = (revenue - fee) - cost
        cash += revenue - fee
        trades.append(pnl)
        holdings = 0

    return SymbolResult(
        symbol=symbol,
        initial=initial_cash,
        final=cash,
        trades=trades,
        max_dd=max_dd,
        sessions=sessions,
        escapes=escapes,
    )


async def main():
    for tf in ["15m", "1h", "4h"]:
        data = await fetch_all(tf)
        if not data:
            continue

        n = len(data)
        per_symbol = INITIAL_CAPITAL / n

        print(f"\n{'='*70}")
        print(f"🎯 TF={tf}  ({n} نماد × {per_symbol:,.0f} تومان)")
        print(f"{'='*70}")

        all_trades = []
        total_final = 0
        total_sessions = 0
        total_escapes = 0
        worst_dd = 0

        for sym, candles in data.items():
            r = backtest_symbol(sym, candles, per_symbol)
            total_final += r.final
            all_trades.extend(r.trades)
            total_sessions += r.sessions
            total_escapes += r.escapes
            worst_dd = max(worst_dd, r.max_dd)

        wins = sum(1 for t in all_trades if t > 0)
        losses = sum(1 for t in all_trades if t <= 0)
        wr = wins / len(all_trades) * 100 if all_trades else 0
        ret = (total_final / INITIAL_CAPITAL - 1) * 100

        print(f"  بازده:       {ret:>+10.2f}%")
        print(f"  سرمایه نهایی: {total_final:>11,.0f}")
        print(f"  Max DD:      {worst_dd:>10.2f}%")
        print(f"  تریدها:      {len(all_trades):>11}")
        print(f"  برد/باخت:    {wins:>5} / {losses}")
        print(f"  WR:          {wr:>10.1f}%")
        print(f"  Sessions:    {total_sessions:>11}")
        print(f"  Escapes:     {total_escapes:>11}")


if __name__ == "__main__":
    asyncio.run(main())
