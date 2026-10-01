"""بهینه‌سازی Simple Bot — نسخه Multiprocessing.

استراتژی:
  1. دریافت داده (async)
  2. پیش‌محاسبه‌ی rule scores با multiprocessing (موازی)
  3. تست ۵۴ ترکیب روی cache (سریع)
"""

import asyncio
import time
from concurrent.futures import ProcessPoolExecutor, as_completed

from app.application.use_cases.get_candles import GetCandlesUseCase
from app.core.config import get_settings
from app.domain.entities.candle import Candle
from app.infrastructure.exchange.wallex.client import WallexExchange
from app.services.bottom_detector import detect_bottom

SYMBOLS = ["BTCTMN", "ETHTMN", "XRPTMN", "DOGETMN", "SOLTMN"]
TF = "15m"
N_CANDLES = 2000
WARMUP = 100
INITIAL_CAPITAL = 300_000
FEE_PCT = 0.2
MAX_POSITIONS = 2
POSITION_SIZE_PCT = 50.0


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


# ============ توابع Worker (باید top-level باشن برای pickle) ============

def _score_one(args):
    """محاسبه‌ی score برای یک کندل — این تابع در process worker اجرا میشه."""
    symbol, idx, window = args
    if idx < WARMUP:
        return (symbol, idx, 0)
    try:
        rule = detect_bottom(window)
        return (symbol, idx, rule.score)
    except Exception:
        return (symbol, idx, 0)


def _score_chunk(chunk):
    """محاسبه‌ی score برای یک chunk از کندل‌ها."""
    return [_score_one(args) for args in chunk]


def precompute_scores_mp(markets_data, n_workers: int = 8, chunk_size: int = 50):
    """پیش‌محاسبه با multiprocessing."""
    print(f"🔄 پیش‌محاسبه با {n_workers} worker...")

    # آماده‌سازی همه‌ی taskها
    all_tasks = []
    for symbol, candles in markets_data.items():
        for idx in range(len(candles)):
            window = candles[: idx + 1]
            all_tasks.append((symbol, idx, window))

    print(f"   کل taskها: {len(all_tasks):,}")
    print(f"   Chunk size: {chunk_size}")
    print(f"   تعداد chunk: {len(all_tasks) // chunk_size + 1}")

    # تقسیم به chunk
    chunks = [
        all_tasks[i : i + chunk_size]
        for i in range(0, len(all_tasks), chunk_size)
    ]

    # اجرای موازی
    scores_per_symbol = {s: [0] * len(candles) for s, candles in markets_data.items()}

    start = time.time()
    completed = 0
    total_chunks = len(chunks)

    with ProcessPoolExecutor(max_workers=n_workers) as pool:
        futures = [pool.submit(_score_chunk, chunk) for chunk in chunks]
        for fut in as_completed(futures):
            results = fut.result()
            for symbol, idx, score in results:
                scores_per_symbol[symbol][idx] = score
            completed += 1
            if completed % max(1, total_chunks // 20) == 0:
                pct = completed / total_chunks * 100
                elapsed = time.time() - start
                print(f"   پیشرفت: {pct:>5.1f}% ({completed}/{total_chunks}) — {elapsed:.1f}s")

    elapsed = time.time() - start
    print(f"✅ پیش‌محاسبه در {elapsed:.1f}s\n")
    return scores_per_symbol


# ============ Backtest سریع (روی cache) ============

def run_config_fast(markets_data, scores_per_symbol, min_score, tp_pct, sl_pct, timeout):
    """اجرای سریع یک config روی cache."""
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
        # چک خروج
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

        # چک ورود
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
        if invest < 10_000:
            continue

        open_positions[symbol] = {
            "entry": entry,
            "tp": entry * (1 + tp_pct / 100),
            "sl": entry * (1 - sl_pct / 100),
            "invest": invest,
            "entry_idx": idx,
        }

    wins = sum(1 for t in trades if t > 0)
    losses = len(trades) - wins
    wr = wins / len(trades) * 100 if trades else 0

    return {
        "return_pct": (capital / INITIAL_CAPITAL - 1) * 100,
        "capital": capital,
        "trades": len(trades),
        "wins": wins,
        "losses": losses,
        "wr": wr,
        "max_dd": max_dd,
    }


# ============ Main ============

async def main():
    print("📥 دریافت داده...\n")
    markets_data = await fetch_all()
    print(f"✅ {len(markets_data)} نماد\n")

    # پیش‌محاسبه موازی
    scores_per_symbol = precompute_scores_mp(markets_data, n_workers=8, chunk_size=50)

    # ترکیب‌ها
    configs = []
    for min_score in [5, 6, 7]:
        for tp in [2.0, 2.5, 3.0]:
            for sl in [1.5]:
                for timeout in [12, 24]:
                    configs.append((min_score, tp, sl, timeout))

    print(f"{'='*90}")
    print(f"{'min_score':>10} {'TP':>6} {'SL':>6} {'timeout':>8} {'ترید':>7} {'WR':>8} {'بازده':>10} {'DD':>8}")
    print(f"{'='*90}")

    start = time.time()
    results = []
    for min_score, tp, sl, timeout in configs:
        r = run_config_fast(markets_data, scores_per_symbol, min_score, tp, sl, timeout)
        results.append({"min_score": min_score, "tp": tp, "sl": sl, "timeout": timeout, **r})
        print(
            f"{min_score:>10} {tp:>6.1f} {sl:>6.1f} {timeout:>8} "
            f"{r['trades']:>7} {r['wr']:>7.1f}% {r['return_pct']:>+9.2f}% {r['max_dd']:>7.2f}%"
        )

    print(f"\n⏱️  زمان تست {len(configs)} ترکیب: {time.time()-start:.1f}s")

    # بهترین‌ها
    print(f"\n{'='*90}")
    best_return = max(results, key=lambda x: x["return_pct"])
    print("🏆 بهترین بازده:")
    print(f"   min_score={best_return['min_score']}, TP={best_return['tp']}, SL={best_return['sl']}, timeout={best_return['timeout']}")
    print(f"   بازده: {best_return['return_pct']:+.2f}%  |  ترید: {best_return['trades']}  |  WR: {best_return['wr']:.1f}%  |  DD: {best_return['max_dd']:.2f}%")

    best_wr = max(results, key=lambda x: x["wr"])
    print("\n🏆 بهترین Win Rate:")
    print(f"   min_score={best_wr['min_score']}, TP={best_wr['tp']}, SL={best_wr['sl']}, timeout={best_wr['timeout']}")
    print(f"   WR: {best_wr['wr']:.1f}%  |  بازده: {best_wr['return_pct']:+.2f}%  |  ترید: {best_wr['trades']}")

    best_dd = min(results, key=lambda x: x["max_dd"])
    print("\n🏆 کمترین DD:")
    print(f"   min_score={best_dd['min_score']}, TP={best_dd['tp']}, SL={best_dd['sl']}, timeout={best_dd['timeout']}")
    print(f"   DD: {best_dd['max_dd']:.2f}%  |  بازده: {best_dd['return_pct']:+.2f}%  |  ترید: {best_dd['trades']}")

    print("\n🏆 بهترین بازده/ریسک:")
    best_ratio = max(results, key=lambda x: x["return_pct"] / (x["max_dd"] + 0.01))
    print(f"   min_score={best_ratio['min_score']}, TP={best_ratio['tp']}, SL={best_ratio['sl']}, timeout={best_ratio['timeout']}")
    print(f"   بازده: {best_ratio['return_pct']:+.2f}%  |  DD: {best_ratio['max_dd']:.2f}%  |  نسبت: {best_ratio['return_pct']/(best_ratio['max_dd']+0.01):.2f}")


if __name__ == "__main__":
    asyncio.run(main())
