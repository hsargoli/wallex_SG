"""تست ربات روی یک روز خاص از گذشته."""

import asyncio
import time
from datetime import datetime, timezone

from app.core.config import get_settings
from app.infrastructure.exchange.wallex.client import WallexExchange
from app.services.simple_bot import (
    FEE_PCT, MAX_POSITIONS, MIN_SCORE, POSITION_SIZE_PCT,
    TIMEOUT_CANDLES, check_simple_exit, make_simple_decision,
)

# ---------- تنظیمات ----------
SYMBOLS = ["BTCTMN", "ETHTMN", "XRPTMN", "DOGETMN", "SOLTMN"]
TF = "15m"
INITIAL_CAPITAL = 300_000

# تاریخ تست — چند روز مختلف
TEST_DAYS = [
    ("2026-09-05", "2026-09-06"),
    ("2026-09-10", "2026-09-11"),
    ("2026-09-15", "2026-09-16"),
    ("2026-09-20", "2026-09-21"),
    ("2026-09-25", "2026-09-26"),
]


async def fetch_day(symbol: str, start_date: str, end_date: str):
    """دریافت کندل‌های یک بازه."""
    settings = get_settings()
    ex = WallexExchange.create(settings)
    try:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        end_dt = datetime.strptime(end_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        start_ts = int(start_dt.timestamp())
        end_ts = int(end_dt.timestamp())
        raw = await ex.get_candles(
            symbol=symbol, resolution="15",
            from_ts=start_ts, to_ts=end_ts,
        )
        return raw
    except Exception:
        return []
    finally:
        await ex.aclose()


async def fetch_all_for_day(start_date: str, end_date: str):
    async def one(sym):
        return sym, await fetch_day(sym, start_date, end_date)
    results = await asyncio.gather(*[one(s) for s in SYMBOLS])
    return {s: c for s, c in results if c}


def simulate_day(markets_data):
    """شبیه‌سازی یک روز روی داده‌های داده‌شده."""
    capital = INITIAL_CAPITAL
    peak = capital
    max_dd = 0.0
    trades = []
    decisions_made = 0

    # رویدادهای زمانی
    events = []
    for symbol, candles in markets_data.items():
        for i, c in enumerate(candles):
            events.append((c.time, symbol, i, c))
    events.sort(key=lambda x: x[0])

    open_positions: dict = {}

    for event_time, symbol, idx, candle in events:
        # چک خروج
        if symbol in open_positions:
            pos = open_positions[symbol]
            should_exit, exit_price, reason = check_simple_exit(
                pos["entry"], pos["tp"], pos["sl"],
                candle, idx - pos["entry_idx"],
            )
            if should_exit:
                pnl_pct = (exit_price / pos["entry"] - 1) * 100 - FEE_PCT
                pnl_tmn = pos["invest"] * pnl_pct / 100
                capital += pnl_tmn
                if capital > peak:
                    peak = capital
                dd = (peak - capital) / peak * 100
                if dd > max_dd:
                    max_dd = dd
                trades.append({
                    "symbol": symbol,
                    "pnl_pct": pnl_pct,
                    "pnl_tmn": pnl_tmn,
                    "reason": reason,
                })
                del open_positions[symbol]

        # چک ورود
        if len(open_positions) >= MAX_POSITIONS:
            continue
        if symbol in open_positions:
            continue

        # حداقل ۱۰۰ کندل برای محاسبه‌ی اندیکاتورها
        # اگه روز کوتاهه، از یه warmup کوچیک استفاده کن
        if idx < 20:
            continue

        window = markets_data[symbol][: idx + 1]
        decision = make_simple_decision(window)
        decisions_made += 1

        if not decision.should_trade:
            continue

        invest = capital * (POSITION_SIZE_PCT / 100)
        invest = min(invest, capital * 0.95)
        if invest < 10_000:
            continue

        open_positions[symbol] = {
            "entry": decision.entry_price,
            "tp": decision.take_profit,
            "sl": decision.stop_loss,
            "invest": invest,
            "entry_idx": idx,
        }

    # بستن پوزیشن‌های باز در پایان روز (با آخرین قیمت)
    for symbol, pos in open_positions.items():
        last_candle = markets_data[symbol][-1]
        exit_price = float(last_candle.close)
        pnl_pct = (exit_price / pos["entry"] - 1) * 100 - FEE_PCT
        pnl_tmn = pos["invest"] * pnl_pct / 100
        capital += pnl_tmn
        trades.append({
            "symbol": symbol,
            "pnl_pct": pnl_pct,
            "pnl_tmn": pnl_tmn,
            "reason": "end_of_day",
        })

    return {
        "capital": capital,
        "return_pct": (capital / INITIAL_CAPITAL - 1) * 100,
        "trades": trades,
        "max_dd": max_dd,
        "decisions": decisions_made,
    }


async def main():
    print(f"🎯 تست ربات روی ۵ روز مختلف")
    print(f"   Config: min_score={MIN_SCORE}, timeout={TIMEOUT_CANDLES}, size={POSITION_SIZE_PCT}%")
    print(f"{'='*80}\n")

    all_results = []

    for start_date, end_date in TEST_DAYS:
        print(f"📅 {start_date} → {end_date}")
        start = time.time()

        markets_data = await fetch_all_for_day(start_date, end_date)
        if not markets_data:
            print(f"   ❌ داده‌ای یافت نشد\n")
            continue

        total_candles = sum(len(c) for c in markets_data.values())
        print(f"   کندل‌ها: {total_candles} از {len(markets_data)} نماد")

        result = simulate_day(markets_data)
        elapsed = time.time() - start

        wins = sum(1 for t in result["trades"] if t["pnl_pct"] > 0)
        losses = len(result["trades"]) - wins
        wr = wins / len(result["trades"]) * 100 if result["trades"] else 0

        print(f"   💰 بازده: {result['return_pct']:+.2f}%  |  ترید: {len(result['trades'])}  |  WR: {wr:.1f}%  |  DD: {result['max_dd']:.2f}%  |  ⏱️ {elapsed:.1f}s")
        print()

        all_results.append({
            "date": start_date,
            "return_pct": result["return_pct"],
            "trades": len(result["trades"]),
            "wins": wins,
            "losses": losses,
            "wr": wr,
            "dd": result["max_dd"],
        })

    # خلاصه
    if all_results:
        print(f"{'='*80}")
        print(f"📊 خلاصه:")
        print(f"{'='*80}")
        total_return = sum(r["return_pct"] for r in all_results)
        total_trades = sum(r["trades"] for r in all_results)
        total_wins = sum(r["wins"] for r in all_results)
        overall_wr = total_wins / total_trades * 100 if total_trades else 0
        avg_return = total_return / len(all_results)

        print(f"  میانگین بازده روزانه: {avg_return:+.2f}%")
        print(f"  مجموع بازده:          {total_return:+.2f}%")
        print(f"  مجموع ترید:           {total_trades}")
        print(f"  WR کل:                {overall_wr:.1f}%")
        print()
        for r in all_results:
            emoji = "🟢" if r["return_pct"] > 0 else "🔴"
            print(f"  {emoji} {r['date']}: {r['return_pct']:+.2f}%  ({r['trades']} ترید، WR {r['wr']:.0f}%)")


if __name__ == "__main__":
    asyncio.run(main())
