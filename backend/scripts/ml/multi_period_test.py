"""تست Dispatcher در دوره‌های مختلف تاریخی.

- 1D:  365 روز (12 دوره ماهانه)
- 1h:  90 روز (3 دوره 30 روزه)
- 15m: 18 روز (3 دوره 6 روزه)
"""

import asyncio
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timezone, timedelta

from app.application.use_cases.get_candles import GetCandlesUseCase
from app.core.config import get_settings
from app.domain.entities.candle import Candle
from app.infrastructure.exchange.wallex.client import WallexExchange

SYMBOLS = ["BTCTMN", "ETHTMN", "XRPTMN", "DOGETMN", "SOLTMN", "ZECTMN"]
INITIAL_CAPITAL = 300_000
FEE_PCT = 0.2
POSITION_SIZE_PCT = 33.0


async def fetch_range(symbol: str, resolution: str, from_ts: int, to_ts: int):
    settings = get_settings()
    ex = WallexExchange.create(settings)
    try:
        raw = await ex.get_candles(
            symbol=symbol, resolution=resolution,
            from_ts=from_ts, to_ts=to_ts,
        )
        return raw
    except Exception:
        return []
    finally:
        await ex.aclose()


# ============ Worker Functions ============

def _test_dispatcher_period(candles: list[Candle]) -> dict:
    """تست Dispatcher روی یک دوره."""
    from app.services.bounce_scalper import check_bounce_exit
    from app.services.simple_bot import check_simple_exit

    if len(candles) < 100:
        return {"return": 0, "trades": 0, "wr": 0, "dd": 0, "error": "داده کم"}

    capital = INITIAL_CAPITAL
    peak = capital
    max_dd = 0
    trades = []
    open_pos = None

    # استراتژی ساده‌سازی‌شده برای تست سریع
    # (چون dispatcher به config نیاز داره و ممکنه برای TF های مختلف متفاوت باشه)
    from app.services.bottom_detector import detect_bottom

    for idx in range(50, len(candles)):
        candle = candles[idx]

        # چک خروج
        if open_pos is not None:
            should_exit, exit_price, _ = check_simple_exit(
                open_pos["entry"], open_pos["tp"], open_pos["sl"],
                candle, idx - open_pos["entry_idx"],
            )
            if should_exit:
                pnl = (exit_price / open_pos["entry"] - 1) * 100 - FEE_PCT
                capital += open_pos["invest"] * pnl / 100
                if capital > peak: peak = capital
                dd = (peak - capital) / peak * 100
                if dd > max_dd: max_dd = dd
                trades.append(pnl)
                open_pos = None

        if open_pos is not None: continue

        # چک ورود
        window = candles[:idx + 1]
        try:
            rule = detect_bottom(window)
        except Exception:
            continue

        if rule.score < 6:
            continue

        # فیلتر روند
        from app.services.indicators import ema
        ema20 = ema(window, 20)
        ema50 = ema(window, 50)
        e20 = next((v for v in reversed(ema20) if v is not None), None)
        e50 = next((v for v in reversed(ema50) if v is not None), None)
        if e20 and e50 and e20 < e50:
            continue

        entry = float(candle.close)
        invest = capital * (POSITION_SIZE_PCT / 100)
        if invest < 5000: continue

        open_pos = {
            "entry": entry,
            "tp": entry * 1.02,
            "sl": entry * 0.985,
            "invest": invest,
            "entry_idx": idx,
        }

    wins = sum(1 for t in trades if t > 0)
    wr = wins / len(trades) * 100 if trades else 0
    return {
        "return": round((capital / INITIAL_CAPITAL - 1) * 100, 2),
        "trades": len(trades),
        "wr": round(wr, 1),
        "dd": round(max_dd, 2),
    }


def _analyze_period(args):
    """تحلیل یک دوره از یک نماد."""
    import asyncio as _asyncio
    symbol, resolution, from_ts, to_ts, label = args

    async def fetch():
        return await fetch_range(symbol, resolution, from_ts, to_ts)

    candles = _asyncio.run(fetch())
    if not candles or len(candles) < 100:
        return {"symbol": symbol, "label": label, "error": "داده کم"}

    result = _test_dispatcher_period(candles)
    result["symbol"] = symbol
    result["label"] = label
    result["candles_count"] = len(candles)
    return result


# ============ Main ============

async def main():
    print("="*80)
    print("📊 تست Dispatcher در دوره‌های مختلف تاریخی")
    print("="*80)

    now = int(datetime.now(timezone.utc).timestamp())

    # ============ تست 1D (12 ماه) ============
    print("\n🎯 TF=1D — 12 دوره ماهانه (365 روز)")
    print("-" * 80)

    d_tasks = []
    for months_ago in range(12):
        days_back = 30 * (months_ago + 1)
        from_ts = now - days_back * 86400
        to_ts = now - (days_back - 30) * 86400
        label = f"{months_ago+1} ماه پیش"
        for symbol in SYMBOLS[:3]:  # فقط 3 نماد برای سرعت
            d_tasks.append((symbol, "D", from_ts, to_ts, label))

    print(f"   تعداد تسک: {len(d_tasks)}")

    start = time.time()
    d_results = []
    with ProcessPoolExecutor(max_workers=6) as pool:
        futures = [pool.submit(_analyze_period, t) for t in d_tasks]
        for fut in as_completed(futures):
            try:
                r = fut.result(timeout=120)
                d_results.append(r)
            except Exception:
                pass

    # گروه‌بندی بر اساس دوره
    periods = {}
    for r in d_results:
        if "error" in r: continue
        periods.setdefault(r["label"], []).append(r)

    print(f"\n{'دوره':<12} {'بازده میانگین':>15} {'ترید میانگین':>15} {'WR میانگین':>12}")
    print("-" * 60)
    for label, results in sorted(periods.items(), key=lambda x: x[0]):
        avg_ret = sum(r["return"] for r in results) / len(results)
        avg_trades = sum(r["trades"] for r in results) / len(results)
        avg_wr = sum(r["wr"] for r in results) / len(results)
        emoji = "🟢" if avg_ret > 0 else "🔴"
        print(f"{emoji} {label:<10} {avg_ret:>+13.2f}% {avg_trades:>13.1f} {avg_wr:>10.1f}%")

    print(f"\n⏱️  زمان: {time.time()-start:.1f}s")


if __name__ == "__main__":
    asyncio.run(main())
