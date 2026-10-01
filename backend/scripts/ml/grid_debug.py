"""Debug: تحلیل دقیق یک session تا باگ رو پیدا کنیم."""

import asyncio

from app.application.use_cases.get_candles import GetCandlesUseCase
from app.core.config import get_settings
from app.infrastructure.exchange.wallex.client import WallexExchange
from app.services.bots.grid_bot.strategy import _calc_adx
from app.services.indicators import atr

INITIAL_CASH = 30_000
FEE_PCT = 0.2
ADX_MAX = 25.0
SPACING_ATR = 1.0
N_LEVELS = 3
CASH_PER_LEVEL_PCT = 15.0
ESCAPE_PCT = 5.0
TIMEOUT_CANDLES = 100


async def main():
    settings = get_settings()
    ex = WallexExchange.create(settings)
    try:
        uc = GetCandlesUseCase(exchange=ex)
        candles = await uc.execute(symbol="BTCTMN", timeframe="15m", limit=2000)
    finally:
        await ex.aclose()

    print(f"📊 BTC کندل‌ها: {len(candles)}")

    cash = INITIAL_CASH
    holdings = 0.0
    avg_buy = 0.0
    peak = INITIAL_CASH
    max_dd = 0.0
    sessions = 0
    escapes = 0
    trades = 0
    session = None

    # Track all equity values to see where DD comes from
    equity_samples = []

    for idx in range(50, len(candles)):
        price = float(candles[idx].close)
        window = candles[: idx + 1]

        equity = cash + holdings * price
        equity_samples.append((idx, equity, cash, holdings, price))

        if equity > peak:
            peak = equity
        dd = (peak - equity) / peak * 100 if peak > 0 else 0
        if dd > max_dd:
            max_dd = dd
            if dd > 10:
                print(f"⚠️  DD جدید {dd:.2f}% — idx={idx} equity={equity:.0f} peak={peak:.0f} cash={cash:.0f} hold={holdings:.6f} price={price:.0f}")

        # شروع session
        if session is None:
            adx = _calc_adx(window, 14)
            if adx >= ADX_MAX:
                continue

            atr_vals = atr(window, 14)
            atr_v = None
            for v in reversed(atr_vals):
                if v is not None:
                    atr_v = v
                    break

            if atr_v is None or atr_v <= 0:
                continue

            spacing = float(atr_v) * SPACING_ATR
            if spacing <= 0 or spacing > price * 0.05:  # spacing نباید بیش از 5% باشه
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
                    "state": "waiting",
                })

            if len(levels) < N_LEVELS:
                continue

            session = {
                "levels": levels,
                "start_price": price,
                "start_idx": idx,
                "spacing": spacing,
            }
            sessions += 1
            print(f"🟢 Session #{sessions} @ idx={idx} price={price:.0f} cash={cash:.0f} spacing={spacing:.0f}")
            continue

        # escape
        diff_pct = abs(price - session["start_price"]) / session["start_price"] * 100
        if diff_pct > ESCAPE_PCT:
            print(f"🔴 Escape @ idx={idx}: diff={diff_pct:.2f}% price={price:.0f} start={session['start_price']:.0f} hold={holdings:.6f}")
            if holdings > 0:
                revenue = holdings * price
                fee = revenue * FEE_PCT / 100
                net = revenue - fee
                cost = holdings * avg_buy
                pnl = net - cost
                cash += net
                print(f"     Sold all: pnl={pnl:.0f} cash_now={cash:.0f}")
                holdings = 0
                avg_buy = 0
            session = None
            escapes += 1
            continue

        # timeout
        if idx - session["start_idx"] > TIMEOUT_CANDLES:
            if holdings > 0:
                revenue = holdings * price
                fee = revenue * FEE_PCT / 100
                net = revenue - fee
                cost = holdings * avg_buy
                pnl = net - cost
                cash += net
                holdings = 0
                avg_buy = 0
            session = None
            continue

        # buy levels
        for lvl in session["levels"]:
            if lvl["state"] == "waiting" and price <= lvl["buy_price"]:
                cost = lvl["qty"] * price
                fee = cost * FEE_PCT / 100
                total = cost + fee
                if total <= cash:
                    cash -= total
                    if holdings > 0:
                        old_cost = avg_buy * holdings
                        holdings += lvl["qty"]
                        avg_buy = (old_cost + cost) / holdings
                    else:
                        holdings = lvl["qty"]
                        avg_buy = price
                    lvl["state"] = "holding"
                    print(f"  🛒 BUY  @ idx={idx}: price={price:.0f} qty={lvl['qty']:.6f} cost={cost:.0f} cash={cash:.0f}")
                else:
                    print(f"  ⚠️  نمی‌تونیم بخریم: total={total:.0f} > cash={cash:.0f}")

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

                lvl["state"] = "waiting"
                trades += 1
                print(f"  💰 SELL @ idx={idx}: price={price:.0f} qty={sell_qty:.6f} pnl={pnl:.0f} cash={cash:.0f} hold={holdings:.6f}")

    # بستن نهایی
    if holdings > 0:
        price = float(candles[-1].close)
        revenue = holdings * price
        fee = revenue * FEE_PCT / 100
        cash += revenue - fee

    print(f"\n{'='*60}")
    print(f"📊 نتیجه:")
    print(f"  سرمایه اولیه: {INITIAL_CASH:,.0f}")
    print(f"  سرمایه نهایی: {cash:,.0f}")
    print(f"  بازده:        {(cash/INITIAL_CASH-1)*100:+.2f}%")
    print(f"  Peak Equity:  {peak:,.0f}")
    print(f"  Max DD:       {max_dd:.2f}%")
    print(f"  Sessions:     {sessions}")
    print(f"  Escapes:      {escapes}")
    print(f"  Trades:       {trades}")
    print(f"\n  🔍 lowest equity samples:")
    equity_samples.sort(key=lambda x: x[1])
    for idx, eq, cash_v, hold_v, price_v in equity_samples[:5]:
        print(f"     idx={idx} equity={eq:.0f} cash={cash_v:.0f} hold={hold_v:.6f} price={price_v:.0f}")


if __name__ == "__main__":
    asyncio.run(main())
