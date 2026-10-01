"""تست ربات روی چند روز — نسخه Multiprocessing.

استراتژی:
  - هر روز رو در یک process جدا اجرا کن
  - یا هر نماد رو در یک process جدا
  - موازی‌سازی درخواست‌های HTTP
"""

import asyncio
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timezone

from app.core.config import get_settings
from app.infrastructure.exchange.wallex.client import WallexExchange
from app.services.simple_bot import (
    FEE_PCT, MAX_POSITIONS, MIN_SCORE, POSITION_SIZE_PCT,
    TIMEOUT_CANDLES, check_simple_exit, make_simple_decision,
)

SYMBOLS = ["BTCTMN", "ETHTMN", "XRPTMN", "DOGETMN", "SOLTMN"]
INITIAL_CAPITAL = 300_000

TEST_DAYS = [
    ("2026-09-05", "2026-09-06"),
    ("2026-09-10", "2026-09-11"),
    ("2026-09-15", "2026-09-16"),
    ("2026-09-20", "2026-09-21"),
    ("2026-09-25", "2026-09-26"),
]


# ============ Worker: دریافت داده برای یک نماد ============

def _fetch_symbol_sync(symbol: str, start_date: str, end_date: str):
    """دریافت کندل برای یک نماد — sync wrapper برای multiprocessing."""
    import asyncio as _asyncio

    async def _inner():
        settings = get_settings()
        ex = WallexExchange.create(settings)
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            end_dt = datetime.strptime(end_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            start_ts = int(start_dt.timestamp())
            end_ts = int(end_dt.timestamp())
            return await ex.get_candles(
                symbol=symbol, resolution="15",
                from_ts=start_ts, to_ts=end_ts,
            )
        except Exception:
            return []
        finally:
            await ex.aclose()

    return symbol, _asyncio.run(_inner())


def _fetch_day_parallel(symbols: list[str], start_date: str, end_date: str, n_workers: int = 5):
    """دریافت موازی کندل‌های همه نمادها در یک روز."""
    with ProcessPoolExecutor(max_workers=n_workers) as pool:
        futures = {
            pool.submit(_fetch_symbol_sync, sym, start_date, end_date): sym
            for sym in symbols
        }
        results = {}
        for fut in as_completed(futures):
            try:
                sym, candles = fut.result(timeout=30)
                if candles:
                    results[sym] = candles
            except Exception:
                pass
    return results


# ============ Worker: شبیه‌سازی یک روز ============

def _simulate_day_sync(args):
    """شبیه‌سازی یک روز — این تابع در process worker اجرا می‌شه."""
    start_date, end_date = args

    markets_data = _fetch_day_parallel(SYMBOLS, start_date, end_date, n_workers=5)
    if not markets_data:
        return {
            "date": start_date,
            "error": "no_data",
            "return_pct": 0,
            "trades": 0,
            "wr": 0,
            "dd": 0,
        }

    # شبیه‌سازی روی این داده
    capital = INITIAL_CAPITAL
    peak = capital
    max_dd = 0.0
    trades = []

    events = []
    for symbol, candles in markets_data.items():
        for i, c in enumerate(candles):
            events.append((c.time, symbol, i, c))
    events.sort(key=lambda x: x[0])

    open_positions: dict = {}

    for event_time, symbol, idx, candle in events:
        # خروج
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
                trades.append(pnl_pct)
                del open_positions[symbol]

        # ورود
        if len(open_positions) >= MAX_POSITIONS:
            continue
        if symbol in open_positions:
            continue
        if idx < 20:
            continue

        window = markets_data[symbol][: idx + 1]
        try:
            decision = make_simple_decision(window)
        except Exception:
            continue

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

    # بستن پوزیشن‌های باز
    for symbol, pos in open_positions.items():
        last_candle = markets_data[symbol][-1]
        exit_price = float(last_candle.close)
        pnl_pct = (exit_price / pos["entry"] - 1) * 100 - FEE_PCT
        pnl_tmn = pos["invest"] * pnl_pct / 100
        capital += pnl_tmn
        trades.append(pnl_pct)

    wins = sum(1 for t in trades if t > 0)
    wr = wins / len(trades) * 100 if trades else 0

    return {
        "date": start_date,
        "return_pct": (capital / INITIAL_CAPITAL - 1) * 100,
        "trades": len(trades),
        "wins": wins,
        "losses": len(trades) - wins,
        "wr": wr,
        "dd": max_dd,
    }


# ============ Main ============

def main():
    print(f"🎯 تست ربات روی {len(TEST_DAYS)} روز (موازی)")
    print(f"   Config: min_score={MIN_SCORE}, timeout={TIMEOUT_CANDLES}, size={POSITION_SIZE_PCT}%")
    print(f"{'='*80}\n")

    start = time.time()

    # اجرای همه‌ی روزها به صورت موازی
    with ProcessPoolExecutor(max_workers=5) as pool:
        futures = {
            pool.submit(_simulate_day_sync, day): day[0]
            for day in TEST_DAYS
        }

        all_results = []
        for fut in as_completed(futures):
            date_key = futures[fut]
            try:
                result = fut.result(timeout=120)
                all_results.append(result)
            except Exception as e:
                print(f"❌ {date_key}: {e}")
                all_results.append({
                    "date": date_key, "error": str(e),
                    "return_pct": 0, "trades": 0, "wr": 0, "dd": 0,
                })

    elapsed = time.time() - start
    all_results.sort(key=lambda x: x["date"])

    print(f"{'='*80}")
    print(f"{'تاریخ':<14} {'بازده':>10} {'ترید':>6} {'WR':>8} {'DD':>8}")
    print(f"{'='*80}")
    for r in all_results:
        if "error" in r and r["error"] != "no_data":
            print(f"{r['date']:<14} ❌ {r['error']}")
            continue
        emoji = "🟢" if r["return_pct"] > 0 else "🔴"
        print(f"{emoji} {r['date']:<12} {r['return_pct']:>+9.2f}% {r['trades']:>6} {r['wr']:>7.1f}% {r['dd']:>7.2f}%")

    # خلاصه
    valid = [r for r in all_results if "error" not in r or r["error"] == "no_data"]
    valid = [r for r in valid if r["trades"] > 0]
    if valid:
        total_return = sum(r["return_pct"] for r in valid)
        total_trades = sum(r["trades"] for r in valid)
        total_wins = sum(r["wins"] for r in valid)
        overall_wr = total_wins / total_trades * 100 if total_trades else 0

        print(f"\n{'='*80}")
        print(f"📊 خلاصه:")
        print(f"{'='*80}")
        print(f"  میانگین بازده:   {total_return/len(valid):+.2f}%")
        print(f"  مجموع بازده:     {total_return:+.2f}%")
        print(f"  مجموع ترید:      {total_trades}")
        print(f"  WR کل:           {overall_wr:.1f}%")

        wins_days = sum(1 for r in valid if r["return_pct"] > 0)
        print(f"  روزهای سودده:    {wins_days}/{len(valid)}")

    print(f"\n⏱️  زمان کل: {elapsed:.1f}s (با {len(TEST_DAYS)} worker موازی)")


if __name__ == "__main__":
    main()
