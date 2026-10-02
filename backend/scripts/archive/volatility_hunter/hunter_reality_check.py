"""Reality check نوسان‌گیر:
  ۱. per-symbol → کدوم بهترین، کدوم بدترین
  ۲. با حذف برندگان → آیا باز هم سودده؟
  ۳. توزیع سود → متمرکز یا یکنواخت؟
"""

import asyncio

from app.application.use_cases.get_candles import GetCandlesUseCase
from app.core.config import get_settings
from app.infrastructure.exchange.wallex.client import WallexExchange
from app.services.bots.volatility_hunter.config import VolatilityHunterConfig
from app.services.bots.volatility_hunter.strategy import evaluate_entry, evaluate_exit

SYMBOLS = [
    "BTCTMN", "ETHTMN", "XRPTMN", "SOLTMN", "BNBTMN",
    "ADATMN", "LINKTMN", "DOGETMN", "DASHTMN", "LTCTMN", "TRXTMN",
    "ZECTMN", "GRAMTMN", "HBARTMN", "UNITMN", "ONETMN",
]
TF = "1h"
N_CANDLES = 2000
INITIAL_CAPITAL = 300_000
FEE_PCT = 0.2
MAX_POSITIONS = 3


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


def backtest_per_symbol(candles, config, cash_per_symbol):
    """Backtest یک نماد مستقل."""
    cash = cash_per_symbol
    holdings = 0.0
    avg_buy = 0.0
    trades = []
    peak = cash_per_symbol
    max_dd = 0
    open_pos = None

    for idx in range(config.warmup_candles, len(candles)):
        candle = candles[idx]
        window = candles[: idx + 1]
        price = float(candle.close)

        equity = cash + holdings * price
        if equity > peak: peak = equity
        dd = (peak - equity) / peak * 100 if peak > 0 else 0
        if dd > max_dd: max_dd = dd

        if open_pos is not None:
            should_exit, exit_p, reason = evaluate_exit(
                window, open_pos["entry"], open_pos["sl"],
                open_pos["tp"], config,
            )
            if should_exit:
                pnl_pct = (exit_p / open_pos["entry"] - 1) * 100 - FEE_PCT
                cash += open_pos["invest"] * pnl_pct / 100
                trades.append({"pnl": pnl_pct, "reason": reason})
                open_pos = None
            continue

        sig = evaluate_entry(window, config)
        if sig is None: continue

        invest = cash * (config.position_size_pct / 100)
        if invest < 5000: continue

        open_pos = {
            "entry": sig.entry_price, "sl": sig.stop_loss,
            "tp": sig.take_profit, "invest": invest,
        }

    if open_pos:
        price = float(candles[-1].close)
        pnl_pct = (price / open_pos["entry"] - 1) * 100 - FEE_PCT
        cash += open_pos["invest"] * pnl_pct / 100
        trades.append({"pnl": pnl_pct, "reason": "end"})

    wins = sum(1 for t in trades if t["pnl"] > 0)
    return {
        "trades": len(trades),
        "wins": wins,
        "wr": wins / len(trades) * 100 if trades else 0,
        "return": (cash / cash_per_symbol - 1) * 100,
        "dd": max_dd,
        "trades_list": trades,
    }


async def main():
    print("📥 دریافت داده...\n")
    data = await fetch_all()
    print(f"✅ {len(data)} نماد\n")

    config = VolatilityHunterConfig()
    per_symbol = INITIAL_CAPITAL / len(data)

    print(f"{'='*80}")
    print(f"🔍 Reality Check — per-symbol independent")
    print(f"{'='*80}")

    print(f"{'symbol':<12} {'ترید':>5} {'WR':>7} {'بازده':>9} {'DD':>7} {'سود کل':>10}")
    print("─" * 65)

    results = {}
    for sym, candles in data.items():
        r = backtest_per_symbol(candles, config, per_symbol)
        results[sym] = r
        emoji = "🟢" if r["return"] > 0 else "🔴"
        profit = r["return"] / 100 * per_symbol
        print(f"{emoji} {sym:<10} {r['trades']:>5} {r['wr']:>6.1f}% {r['return']:>+8.2f}% {r['dd']:>6.1f}% {profit:>+9,.0f}")

    # خلاصه
    total_return = sum(r["return"] for r in results.values()) / len(results)
    total_trades = sum(r["trades"] for r in results.values())
    total_wins = sum(r["wins"] for r in results.values())
    worst_dd = max(r["dd"] for r in results.values())

    print(f"\n{'='*80}")
    print(f"📊 خلاصه:")
    print(f"  میانگین بازده:  {total_return:+.2f}%")
    print(f"  ترید کل:        {total_trades}")
    print(f"  WR کل:          {total_wins/total_trades*100:.1f}%")
    print(f"  بدترین DD:      {worst_dd:.2f}%")

    # تست حذف برندگان
    print(f"\n🎯 تست حذف برندگان:")

    winners = sorted(results.items(), key=lambda x: -x[1]["return"])
    # حذف 3 برنده‌ی اول
    remaining = {k: v for k, v in winners[3:]}
    if remaining:
        avg_without = sum(r["return"] for r in remaining.values()) / len(remaining)
        trades_without = sum(r["trades"] for r in remaining.values())
        print(f"  بدون ۳ برنده:  بازده {avg_without:+.2f}%  |  ترید {trades_without}")

    # حذف ۵ برنده
    remaining5 = {k: v for k, v in winners[5:]}
    if remaining5:
        avg_without5 = sum(r["return"] for r in remaining5.values()) / len(remaining5)
        print(f"  بدون ۵ برنده:  بازده {avg_without5:+.2f}%")


if __name__ == "__main__":
    asyncio.run(main())
