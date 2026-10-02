"""دیباگ تریدهای trend_follow — چرا ضرر می‌ده؟"""
import asyncio
from collections import Counter

from app.application.use_cases.get_candles import GetCandlesUseCase
from app.core.config import get_settings
from app.infrastructure.exchange.wallex.client import WallexExchange
from app.services.regime_detector import detect_regime
from app.services.bots.trend_follow.config import TrendFollowConfig
from app.services.bots.trend_follow.strategy import evaluate_entry, evaluate_exit

SYMBOLS = ["ZECTMN", "DASHTMN", "BNBTMN", "HBARTMN", "SOLTMN", "BTCTMN"]
TF = "1h"
N = 2000


async def fetch_one(sym, settings):
    ex = WallexExchange.create(settings)
    try:
        uc = GetCandlesUseCase(exchange=ex)
        return sym, await uc.execute(symbol=sym, timeframe=TF, limit=N)
    finally:
        await ex.aclose()


def backtest_tf(sym, candles, cash=20000):
    cfg = TrendFollowConfig()
    open_pos = None
    trades = []
    last_exit = -999

    for idx in range(100, len(candles)):
        window = candles[:idx+1]
        price = float(candles[idx].close)

        if open_pos is not None:
            td = open_pos.get("trailing_distance") or (open_pos["entry"] * 0.03)
            tx = evaluate_exit(window, open_pos["entry"], open_pos["sl"],
                               td, cfg, idx - open_pos["entry_idx"])
            if tx.should_exit:
                exit_p = open_pos["sl"] if tx.reason in ("initial_sl", "trailing_sl") else price
                pnl = (exit_p / open_pos["entry"] - 1) * 100 - 0.2
                cash += open_pos["invest"] * pnl / 100
                trades.append({
                    "entry_idx": open_pos["entry_idx"], "exit_idx": idx,
                    "entry": open_pos["entry"], "exit": exit_p,
                    "sl": open_pos["sl"], "pnl": pnl,
                    "reason": tx.reason,
                    "duration": idx - open_pos["entry_idx"],
                })
                open_pos = None
                last_exit = idx
                continue

        if open_pos is not None or idx - last_exit < 3:
            continue

        r = detect_regime(window)
        if r.regime.value != "trending_up":
            continue

        sig = evaluate_entry(window, cfg)
        if sig and sig.should_enter:
            invest = cash * 0.9
            open_pos = {
                "entry": sig.entry_price, "sl": sig.initial_sl,
                "invest": invest, "entry_idx": idx,
                "trailing_distance": sig.trailing_distance,
            }

    return trades


async def main():
    settings = get_settings()
    results = await asyncio.gather(*[fetch_one(s, settings) for s in SYMBOLS])

    all_reasons = Counter()
    all_durations = []

    for sym, candles in results:
        if not candles:
            continue
        trades = backtest_tf(sym, candles)

        wins = [t for t in trades if t["pnl"] > 0]
        losses = [t for t in trades if t["pnl"] <= 0]
        total_pnl = sum(t["pnl"] for t in trades) / len(trades) if trades else 0

        print(f"\n{'='*80}")
        print(f"📊 {sym}: {len(trades)} ترید | برد={len(wins)} باخت={len(losses)} | میانگین pnl={total_pnl:+.2f}%")
        print(f"{'='*80}")
        print(f"  {'#':>3} {'entry':>10} {'exit':>10} {'pnl%':>8} {'dur':>4} {'reason':<15}")
        print(f"  {'─'*70}")
        for i, t in enumerate(trades[:12], 1):  # فقط 12 تای اول
            emoji = "🟢" if t["pnl"] > 0 else "🔴"
            print(f"  {emoji}{i:>2} {t['entry']:>10.2f} {t['exit']:>10.2f} "
                  f"{t['pnl']:>+7.2f}% {t['duration']:>4} {t['reason']:<15}")
            all_reasons[t["reason"]] += 1
            all_durations.append(t["duration"])

    print(f"\n{'='*80}")
    print(f"📊 خلاصه:")
    print(f"  توزیع دلایل خروج:")
    for reason, count in all_reasons.most_common():
        print(f"    {reason:<20} {count:>4}")
    if all_durations:
        avg_dur = sum(all_durations) / len(all_durations)
        print(f"  میانگین مدت: {avg_dur:.1f} کندل")


if __name__ == "__main__":
    asyncio.run(main())
