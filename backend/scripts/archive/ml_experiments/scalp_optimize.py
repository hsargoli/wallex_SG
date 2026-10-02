"""Scalp Optimizer — بهینه‌سازی برای ترید زیاد با TP کم.

استراتژی:
  - TP: 0.8% تا 2.0%
  - SL: 0.5% تا 1.2%
  - min_score: 4 تا 6
  - همه با فیلتر روند EMA20 > EMA50
  - کارمزد: 0.2%
"""

import asyncio
import time
from concurrent.futures import ProcessPoolExecutor, as_completed

from app.application.use_cases.get_candles import GetCandlesUseCase
from app.core.config import get_settings
from app.domain.entities.candle import Candle
from app.infrastructure.exchange.wallex.client import WallexExchange
from app.services.bottom_detector import detect_bottom
from app.services.indicators import ema

SYMBOLS = ["BTCTMN", "ETHTMN", "XRPTMN", "DOGETMN", "SOLTMN"]
TF = "15m"
N_CANDLES = 2000
WARMUP = 50
INITIAL_CAPITAL = 300_000
FEE_PCT = 0.2
MAX_POSITIONS = 3
POSITION_SIZE_PCT = 33.0  # 3 پوزیشن × 33% = ~100%


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


# ============ Worker: precompute scores ============

def _precompute_chunk(args):
    """پیش‌محاسبه‌ی score و trend برای یک chunk."""
    symbol, chunks = args
    result = []
    for idx, window, trend_ok in chunks:
        if not trend_ok or idx < WARMUP:
            result.append((symbol, idx, 0))
            continue
        try:
            rule = detect_bottom(window)
            result.append((symbol, idx, rule.score))
        except Exception:
            result.append((symbol, idx, 0))
    return result


def _extract_tasks(markets_data):
    """استخراج همه‌ی taskها (فقط اونایی که روند بالاست)."""
    tasks = []
    for symbol, candles in markets_data.items():
        # محاسبه‌ی EMA برای کل سری یک‌بار
        ema20_vals = ema(candles, 20)
        ema50_vals = ema(candles, 50)

        for idx in range(len(candles)):
            trend_ok = False
            if idx >= 50:
                e20 = next((v for v in reversed(ema20_vals[:idx+1]) if v is not None), None)
                e50 = next((v for v in reversed(ema50_vals[:idx+1]) if v is not None), None)
                if e20 and e50:
                    trend_ok = e20 > e50

            tasks.append((idx, candles[:idx+1], trend_ok))

    return tasks


def precompute_all(markets_data, n_workers=8, chunk_size=100):
    """پیش‌محاسبه‌ی موازی score."""
    print(f"🔄 پیش‌محاسبه‌ی score برای {len(markets_data)} نماد...")

    # آماده‌سازی taskها به ازای هر نماد
    tasks_by_symbol = {}
    for symbol, candles in markets_data.items():
        print(f"   آماده‌سازی {symbol}...", end="", flush=True)
        tasks_by_symbol[symbol] = _extract_tasks({symbol: candles})
        print(f" {len(tasks_by_symbol[symbol])} task")

    # اجرای موازی
    scores_per_symbol = {s: [0] * len(candles) for s, candles in markets_data.items()}

    jobs = []
    for symbol, tasks in tasks_by_symbol.items():
        for i in range(0, len(tasks), chunk_size):
            jobs.append((symbol, tasks[i:i+chunk_size]))

    print(f"\n   کل jobها: {len(jobs)} (chunk_size={chunk_size})")
    start = time.time()

    with ProcessPoolExecutor(max_workers=n_workers) as pool:
        futures = [pool.submit(_precompute_chunk, job) for job in jobs]
        completed = 0
        for fut in as_completed(futures):
            results = fut.result()
            for symbol, idx, score in results:
                scores_per_symbol[symbol][idx] = score
            completed += 1
            if completed % max(1, len(jobs) // 10) == 0:
                pct = completed / len(jobs) * 100
                print(f"   {pct:.0f}%  ({completed}/{len(jobs)})  {time.time()-start:.1f}s")

    print(f"✅ پیش‌محاسبه در {time.time()-start:.1f}s\n")
    return scores_per_symbol


# ============ Backtest سریع ============

def run_config(markets_data, scores_per_symbol, min_score, tp_pct, sl_pct, timeout):
    """اجرای سریع یک config."""
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
            exit_price = None
            if candle.high >= pos["tp"]:
                exit_price = pos["tp"]
            elif candle.low <= pos["sl"]:
                exit_price = pos["sl"]
            elif idx - pos["entry_idx"] >= timeout:
                exit_price = float(candle.close)

            if exit_price is not None:
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
        if idx < WARMUP:
            continue
        if scores_per_symbol[symbol][idx] < min_score:
            continue

        entry = float(candle.close)
        invest = capital * (POSITION_SIZE_PCT / 100)
        invest = min(invest, capital * 0.95)
        if invest < 5_000:
            continue

        open_positions[symbol] = {
            "entry": entry,
            "tp": entry * (1 + tp_pct / 100),
            "sl": entry * (1 - sl_pct / 100),
            "invest": invest,
            "entry_idx": idx,
        }

    wins = sum(1 for t in trades if t > 0)
    wr = wins / len(trades) * 100 if trades else 0

    return {
        "return_pct": (capital / INITIAL_CAPITAL - 1) * 100,
        "trades": len(trades),
        "wins": wins,
        "wr": wr,
        "max_dd": max_dd,
    }


# ============ Main ============

async def main():
    print("📥 دریافت داده...\n")
    markets_data = await fetch_all()
    print(f"✅ {len(markets_data)} نماد\n")

    scores_per_symbol = precompute_all(markets_data, n_workers=8, chunk_size=100)

    # گرید جستجو — TP کم، SL کوچک، ترید زیاد
    configs = []
    for min_score in [4, 5]:
        for tp in [0.8, 1.0, 1.2, 1.5, 2.0]:
            for sl in [0.5, 0.8, 1.0, 1.2]:
                for timeout in [8, 12, 16]:
                    configs.append((min_score, tp, sl, timeout))

    print(f"{'='*95}")
    print(f"{'score':>5} {'TP':>5} {'SL':>5} {'TO':>4} {'ترید':>6} {'WR':>7} {'بازده':>10} {'DD':>7} {'R/DD':>6}")
    print(f"{'='*95}")

    results = []
    start = time.time()
    for min_score, tp, sl, timeout in configs:
        r = run_config(markets_data, scores_per_symbol, min_score, tp, sl, timeout)
        r.update({"min_score": min_score, "tp": tp, "sl": sl, "timeout": timeout})
        results.append(r)
        rdd = r["return_pct"] / (r["max_dd"] + 0.01) if r["max_dd"] >= 0 else 0
        print(f"{min_score:>5} {tp:>5.1f} {sl:>5.1f} {timeout:>4} {r['trades']:>6} {r['wr']:>6.1f}% {r['return_pct']:>+9.2f}% {r['max_dd']:>6.2f}% {rdd:>6.2f}")

    print(f"\n⏱️  زمان تست {len(configs)} ترکیب: {time.time()-start:.1f}s")

    # فیلتر: ترید >= 100
    valid = [r for r in results if r["trades"] >= 100]
    if not valid:
        valid = results

    # بهترین‌ها
    print(f"\n{'='*95}")
    print("🏆 بهترین بازده (با ترید >= 100):")
    best = max(valid, key=lambda x: x["return_pct"])
    print(f"   score={best['min_score']}, TP={best['tp']}, SL={best['sl']}, TO={best['timeout']}")
    print(f"   بازده: {best['return_pct']:+.2f}%  |  ترید: {best['trades']}  |  WR: {best['wr']:.1f}%  |  DD: {best['max_dd']:.2f}%")

    print("\n🏆 بیشترین ترید:")
    most = max(results, key=lambda x: x["trades"])
    print(f"   score={most['min_score']}, TP={most['tp']}, SL={most['sl']}, TO={most['timeout']}")
    print(f"   ترید: {most['trades']}  |  بازده: {most['return_pct']:+.2f}%  |  WR: {most['wr']:.1f}%")

    print("\n🏆 بهترین R/DD:")
    best_rdd = max(valid, key=lambda x: x["return_pct"] / (x["max_dd"] + 0.01))
    print(f"   score={best_rdd['min_score']}, TP={best_rdd['tp']}, SL={best_rdd['sl']}, TO={best_rdd['timeout']}")
    print(f"   بازده: {best_rdd['return_pct']:+.2f}%  |  DD: {best_rdd['max_dd']:.2f}%  |  ترید: {best_rdd['trades']}")


if __name__ == "__main__":
    asyncio.run(main())
