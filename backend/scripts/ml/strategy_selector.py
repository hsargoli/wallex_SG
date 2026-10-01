"""استراتژی‌سنج — انتخاب بهترین استراتژی برای هر ارز.

استراتژی:
  ۱. داده رو به ۳ دوره تقسیم می‌کنیم
  ۲. هر استراتژی رو روی هر دوره تست می‌کنیم (موازی با MP)
  ۳. استراتژی برنده = بالاترین میانگین در همه دوره‌ها
  ۴. خروجی JSON برای dispatcher

MULTIPROCESSING: هر نماد در یک process جدا
"""

import asyncio
import json
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

from app.application.use_cases.get_candles import GetCandlesUseCase
from app.core.config import get_settings
from app.domain.entities.candle import Candle
from app.infrastructure.exchange.wallex.client import WallexExchange

SYMBOLS = [
    "BTCTMN", "ETHTMN", "XRPTMN", "DOGETMN", "SOLTMN",
    "BNBTMN", "ADATMN", "LINKTMN", "HBARTMN", "DASHTMN",
    "TRXTMN", "LTCTMN", "UNITMN", "ZECTMN", "GRAMTMN",
]
TF = "15m"
N_CANDLES = 2000
INITIAL_CAPITAL = 300_000
FEE_PCT = 0.2
POSITION_SIZE_PCT = 33.0
N_SPLITS = 3
OUTPUT_FILE = Path("data/strategy_config.json")


# ============ Worker: fetch + analyze ============

def _analyze_symbol(symbol: str) -> dict:
    """این تابع در process worker اجرا می‌شه."""
    import asyncio as _asyncio

    async def fetch():
        settings = get_settings()
        ex = WallexExchange.create(settings)
        try:
            uc = GetCandlesUseCase(exchange=ex)
            return await uc.execute(symbol=symbol, timeframe=TF, limit=N_CANDLES)
        except Exception:
            return []
        finally:
            await ex.aclose()

    candles = _asyncio.run(fetch())
    if len(candles) < 300:
        return {"symbol": symbol, "error": "dاده کم"}

    # تقسیم به N_SPLITS دوره
    n = len(candles)
    chunk = n // N_SPLITS

    # نتایج هر استراتژی در هر دوره
    strategies = ["simple", "bounce", "grid"]
    results: dict = {s: [] for s in strategies}

    for i in range(N_SPLITS):
        start = i * chunk
        end = (i + 1) * chunk if i < N_SPLITS - 1 else n
        period_candles = candles[start:end]

        if len(period_candles) < 100:
            continue

        results["simple"].append(_run_simple(period_candles))
        results["bounce"].append(_run_bounce(period_candles))
        results["grid"].append(_run_grid(period_candles))

    # میانگین
    summary = {}
    for s, returns in results.items():
        if returns:
            avg = sum(returns) / len(returns)
            # پایداری: نسبت دوره‌های سودده
            stability = sum(1 for r in returns if r > 0) / len(returns)
            summary[s] = {
                "avg_return": round(avg, 2),
                "stability": round(stability, 2),
                "periods": [round(r, 2) for r in returns],
            }
        else:
            summary[s] = {"avg_return": -999, "stability": 0, "periods": []}

    # بهترین = بالاترین avg_return با در نظر گرفتن stability
    def score(s):
        # ترکیب avg و stability
        return summary[s]["avg_return"] * 0.6 + summary[s]["stability"] * 20 * 0.4

    best = max(strategies, key=score)

    return {
        "symbol": symbol,
        "best_strategy": best,
        "summary": summary,
        "total_candles": len(candles),
    }


def _run_simple(candles: list[Candle]) -> float:
    from app.services.simple_bot import check_simple_exit, make_simple_decision

    capital = INITIAL_CAPITAL
    open_pos = None

    for idx in range(50, len(candles)):
        candle = candles[idx]

        if open_pos is not None:
            should_exit, exit_price, _ = check_simple_exit(
                open_pos["entry"], open_pos["tp"], open_pos["sl"],
                candle, idx - open_pos["entry_idx"],
            )
            if should_exit:
                pnl = (exit_price / open_pos["entry"] - 1) * 100 - FEE_PCT
                capital += open_pos["invest"] * pnl / 100
                open_pos = None

        if open_pos is not None:
            continue

        window = candles[: idx + 1]
        try:
            d = make_simple_decision(window)
        except Exception:
            continue
        if not d.should_trade:
            continue

        invest = capital * (POSITION_SIZE_PCT / 100)
        if invest < 5000:
            continue

        open_pos = {
            "entry": d.entry_price, "tp": d.take_profit, "sl": d.stop_loss,
            "invest": invest, "entry_idx": idx,
        }

    return (capital / INITIAL_CAPITAL - 1) * 100


def _run_bounce(candles: list[Candle]) -> float:
    from app.services.bounce_scalper import check_bounce_exit, make_bounce_decision

    capital = INITIAL_CAPITAL
    open_pos = None

    for idx in range(50, len(candles)):
        candle = candles[idx]

        if open_pos is not None:
            should_exit, exit_price, _ = check_bounce_exit(
                open_pos["entry"], open_pos["tp"], open_pos["sl"],
                candle, idx - open_pos["entry_idx"],
            )
            if should_exit:
                pnl = (exit_price / open_pos["entry"] - 1) * 100 - FEE_PCT
                capital += open_pos["invest"] * pnl / 100
                open_pos = None

        if open_pos is not None:
            continue

        window = candles[: idx + 1]
        try:
            d = make_bounce_decision(window)
        except Exception:
            continue
        if not d.should_trade:
            continue

        invest = capital * (POSITION_SIZE_PCT / 100)
        if invest < 5000:
            continue

        open_pos = {
            "entry": d.entry_price, "tp": d.take_profit, "sl": d.stop_loss,
            "invest": invest, "entry_idx": idx,
        }

    return (capital / INITIAL_CAPITAL - 1) * 100


def _run_grid(candles: list[Candle]) -> float:
    from app.services.grid_bot import calculate_grid_state, plan_grid

    capital = INITIAL_CAPITAL
    active_plan = None
    active_state = None

    for idx in range(50, len(candles)):
        candle = candles[idx]
        price = float(candle.close)

        if active_plan is not None:
            state = calculate_grid_state(active_plan, price)
            active_state = state
            if state.filled_levels:
                if price >= state.take_profit:
                    pnl = (state.take_profit / state.avg_price - 1) * 100 - FEE_PCT
                    capital += state.total_invested * pnl / 100
                    active_plan = None
                    active_state = None
                    continue
                if price <= active_plan.hard_stop_loss:
                    pnl = (active_plan.hard_stop_loss / state.avg_price - 1) * 100 - FEE_PCT
                    capital += state.total_invested * pnl / 100
                    active_plan = None
                    active_state = None
                    continue
            continue

        window = candles[: idx + 1]
        try:
            plan = plan_grid(window, "x", capital * (POSITION_SIZE_PCT / 100))
        except Exception:
            continue
        if plan is None or not plan.should_start:
            continue

        active_plan = plan
        active_state = calculate_grid_state(plan, price)

    if active_plan and active_state and active_state.filled_levels:
        last = candles[-1]
        pnl = (float(last.close) / active_state.avg_price - 1) * 100 - FEE_PCT
        capital += active_state.total_invested * pnl / 100

    return (capital / INITIAL_CAPITAL - 1) * 100


# ============ Main ============

def main():
    print(f"🎯 Strategy Selector — {len(SYMBOLS)} نماد × {N_SPLITS} دوره")
    print(f"   Multiprocessing: {len(SYMBOLS)} workers\n")

    start = time.time()
    results = []

    with ProcessPoolExecutor(max_workers=len(SYMBOLS)) as pool:
        futures = {pool.submit(_analyze_symbol, sym): sym for sym in SYMBOLS}
        for fut in as_completed(futures):
            sym = futures[fut]
            try:
                r = fut.result(timeout=120)
                results.append(r)
                if "error" in r:
                    print(f"  ❌ {sym}: {r['error']}")
                else:
                    best = r["best_strategy"]
                    summ = r["summary"][best]
                    print(f"  ✅ {sym:10} → {best:8} (avg={summ['avg_return']:+.2f}%, stab={summ['stability']:.0%})")
            except Exception as e:
                print(f"  ❌ {sym}: {e}")

    # ذخیره config
    config = {}
    for r in results:
        if "error" in r:
            continue
        config[r["symbol"]] = {
            "best_strategy": r["best_strategy"],
            "summary": r["summary"],
        }

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(json.dumps(config, indent=2, ensure_ascii=False))

    print(f"\n{'='*70}")
    print(f"📊 خلاصه:")
    print(f"{'='*70}")

    from collections import Counter
    best_counts = Counter(r["best_strategy"] for r in results if "error" not in r)
    for strat, count in best_counts.most_common():
        assets = [r["symbol"] for r in results if r.get("best_strategy") == strat]
        print(f"  {strat:10}: {count} نماد  →  {', '.join(assets)}")

    print(f"\n💾 Config ذخیره شد: {OUTPUT_FILE}")
    print(f"⏱️  زمان کل: {time.time()-start:.1f}s")


if __name__ == "__main__":
    main()
