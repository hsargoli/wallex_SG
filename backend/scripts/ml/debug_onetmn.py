"""دیباگ ONETMN — چرا +147%؟"""
import asyncio

from app.application.use_cases.get_candles import GetCandlesUseCase
from app.core.config import get_settings
from app.infrastructure.exchange.wallex.client import WallexExchange
from app.services.regime_detector import detect_regime
from app.services.bots.trend_follow.config import TrendFollowConfig
from app.services.bots.trend_follow.strategy import evaluate_entry, evaluate_exit

SYMBOL = "ONETMN"
TF = "1h"
N = 2000


async def main():
    settings = get_settings()
    ex = WallexExchange.create(settings)
    try:
        uc = GetCandlesUseCase(exchange=ex)
        candles = await uc.execute(symbol=SYMBOL, timeframe=TF, limit=N)
    finally:
        await ex.aclose()

    print(f"📊 {SYMBOL} — {len(candles)} کندل")
    print(f"💰 قیمت اول: {candles[0].close}")
    print(f"💰 قیمت آخر: {candles[-1].close}")
    print(f"📈 تغییر کل: {(float(candles[-1].close)/float(candles[0].close)-1)*100:+.2f}%")
    print()

    cfg = TrendFollowConfig()
    cash = 20000.0
    cash_initial = cash
    open_pos = None
    trades = []

    for idx in range(100, len(candles)):
        window = candles[:idx+1]
        price = float(candles[idx].close)

        # خروج
        if open_pos is not None:
            trailing_dist = open_pos.get("trailing_distance") or (open_pos["entry"] * 0.03)
            tx = evaluate_exit(
                window, open_pos["entry"], open_pos["sl"],
                trailing_dist, cfg, idx - open_pos["entry_idx"],
            )
            if tx.should_exit:
                exit_p = open_pos["sl"] if tx.reason in ("initial_sl", "trailing_sl") else price
                pnl = (exit_p / open_pos["entry"] - 1) * 100 - 0.2
                cash += open_pos["invest"] * pnl / 100
                trades.append({
                    "idx": open_pos["entry_idx"],
                    "exit_idx": idx,
                    "entry": open_pos["entry"],
                    "exit": exit_p,
                    "pnl": pnl,
                    "reason": tx.reason,
                    "invest": open_pos["invest"],
                    "cash_after": cash,
                })
                open_pos = None
                continue

        # ورود
        if open_pos is not None:
            continue

        r = detect_regime(window)
        if r.regime.value != "trending_up":
            continue

        sig = evaluate_entry(window, cfg)
        if sig and sig.should_enter:
            invest = cash * 0.9
            open_pos = {
                "entry": sig.entry_price,
                "sl": sig.initial_sl,
                "invest": invest,
                "entry_idx": idx,
                "trailing_distance": sig.trailing_distance,
            }

    print(f"{'idx':>5} {'→exit':>6} {'entry':>12} {'exit':>12} {'pnl%':>8} {'reason':<12} {'invest':>10} {'cash':>10}")
    print(f"{'─'*90}")
    for t in trades:
        print(f"{t['idx']:>5} {t['exit_idx']:>6} {t['entry']:>12.2f} {t['exit']:>12.2f} "
              f"{t['pnl']:>+7.2f}% {t['reason']:<12} {t['invest']:>10,.0f} {t['cash_after']:>10,.0f}")

    final_ret = (cash / cash_initial - 1) * 100
    print(f"\n📊 نتیجه: {cash_initial:,.0f} → {cash:,.0f} ({final_ret:+.2f}%)")


if __name__ == "__main__":
    asyncio.run(main())
