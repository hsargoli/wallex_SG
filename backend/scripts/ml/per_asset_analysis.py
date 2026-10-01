"""تحلیل هر نماد به صورت جداگانه — کدوم استراتژی بهتره؟

برای هر نماد:
  ۱. Grid Bot
  ۲. Bounce Scalper
  ۳. Simple Bot (کف‌شناسی)
  
مقایسه می‌کنیم و بهترین رو انتخاب می‌کنیم.
"""

import asyncio
import time

from app.application.use_cases.get_candles import GetCandlesUseCase
from app.core.config import get_settings
from app.infrastructure.exchange.wallex.client import WallexExchange
from app.services.bounce_scalper import check_bounce_exit, make_bounce_decision
from app.services.grid_bot import calculate_grid_state, plan_grid
from app.services.simple_bot import check_simple_exit, make_simple_decision

SYMBOLS = ["BTCTMN", "ETHTMN", "XRPTMN", "DOGETMN", "SOLTMN", "BNBTMN", "ADATMN", "LINKTMN", "HBARTMN", "DASHTMN"]
TF = "15m"
N_CANDLES = 2000
INITIAL_CAPITAL = 300_000
FEE_PCT = 0.2
MAX_POSITIONS = 3
POSITION_SIZE_PCT = 33.0


async def fetch_one(sym):
    settings = get_settings()
    ex = WallexExchange.create(settings)
    try:
        uc = GetCandlesUseCase(exchange=ex)
        return sym, await uc.execute(symbol=sym, timeframe=TF, limit=N_CANDLES)
    except Exception:
        return sym, []
    finally:
        await ex.aclose()


# ============ استراتژی ۱: Simple Bot ============
def test_simple(candles):
    capital = INITIAL_CAPITAL
    peak = capital
    max_dd = 0
    trades = []
    open_pos = None

    for idx in range(100, len(candles)):
        candle = candles[idx]

        if open_pos is not None:
            should_exit, exit_price, reason = check_simple_exit(
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

        window = candles[:idx + 1]
        try:
            d = make_simple_decision(window)
        except Exception:
            continue
        if not d.should_trade: continue

        invest = capital * (POSITION_SIZE_PCT / 100)
        invest = min(invest, capital * 0.95)
        if invest < 5000: continue

        open_pos = {
            "entry": d.entry_price,
            "tp": d.take_profit,
            "sl": d.stop_loss,
            "invest": invest,
            "entry_idx": idx,
        }

    wins = sum(1 for t in trades if t > 0)
    wr = wins / len(trades) * 100 if trades else 0
    return {
        "return": (capital / INITIAL_CAPITAL - 1) * 100,
        "trades": len(trades),
        "wr": wr,
        "dd": max_dd,
    }


# ============ استراتژی ۲: Bounce Scalper ============
def test_bounce(candles):
    capital = INITIAL_CAPITAL
    peak = capital
    max_dd = 0
    trades = []
    open_pos = None

    for idx in range(50, len(candles)):
        candle = candles[idx]

        if open_pos is not None:
            should_exit, exit_price, reason = check_bounce_exit(
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

        window = candles[:idx + 1]
        try:
            d = make_bounce_decision(window)
        except Exception:
            continue
        if not d.should_trade: continue

        invest = capital * (POSITION_SIZE_PCT / 100)
        invest = min(invest, capital * 0.95)
        if invest < 5000: continue

        open_pos = {
            "entry": d.entry_price,
            "tp": d.take_profit,
            "sl": d.stop_loss,
            "invest": invest,
            "entry_idx": idx,
        }

    wins = sum(1 for t in trades if t > 0)
    wr = wins / len(trades) * 100 if trades else 0
    return {
        "return": (capital / INITIAL_CAPITAL - 1) * 100,
        "trades": len(trades),
        "wr": wr,
        "dd": max_dd,
    }


# ============ استراتژی ۳: Grid ============
def test_grid(candles):
    capital = INITIAL_CAPITAL
    peak = capital
    max_dd = 0
    trades = []
    active_plan = None
    active_state = None

    for idx in range(50, len(candles)):
        candle = candles[idx]
        price = float(candle.close)

        # چک خروج
        if active_plan is not None:
            state = calculate_grid_state(active_plan, price)
            active_state = state

            if state.filled_levels:
                if price >= state.take_profit:
                    pnl = (state.take_profit / state.avg_price - 1) * 100 - FEE_PCT
                    capital += state.total_invested * pnl / 100
                    if capital > peak: peak = capital
                    dd = (peak - capital) / peak * 100
                    if dd > max_dd: max_dd = dd
                    trades.append(pnl)
                    active_plan = None
                    active_state = None
                    continue
                if price <= active_plan.hard_stop_loss:
                    pnl = (active_plan.hard_stop_loss / state.avg_price - 1) * 100 - FEE_PCT
                    capital += state.total_invested * pnl / 100
                    dd = (peak - capital) / peak * 100
                    if dd > max_dd: max_dd = dd
                    trades.append(pnl)
                    active_plan = None
                    active_state = None
                    continue
            continue

        # گرید جدید
        window = candles[:idx + 1]
        try:
            plan = plan_grid(window, "x", capital * (POSITION_SIZE_PCT / 100))
        except Exception:
            continue
        if plan is None or not plan.should_start:
            continue

        active_plan = plan
        active_state = calculate_grid_state(plan, price)

    # بستن
    if active_plan and active_state and active_state.filled_levels:
        last = candles[-1]
        pnl = (float(last.close) / active_state.avg_price - 1) * 100 - FEE_PCT
        capital += active_state.total_invested * pnl / 100
        trades.append(pnl)

    wins = sum(1 for t in trades if t > 0)
    wr = wins / len(trades) * 100 if trades else 0
    return {
        "return": (capital / INITIAL_CAPITAL - 1) * 100,
        "trades": len(trades),
        "wr": wr,
        "dd": max_dd,
    }


async def main():
    print("📥 دریافت ۱۰ نماد...\n")

    results = {}
    for sym in SYMBOLS:
        s, candles = await fetch_one(sym)
        if not candles or len(candles) < 200:
            print(f"  ❌ {sym}: داده کم")
            continue
        results[s] = candles
        print(f"  ✅ {sym}: {len(candles)} کندل")

    print(f"\n{'='*90}")
    print(f"{'نماد':<10} {'Simple':>12} {'Bounce':>12} {'Grid':>12} {'بهترین':>15}")
    print(f"{'='*90}")

    per_asset_best = {}
    for sym, candles in results.items():
        r_simple = test_simple(candles)
        r_bounce = test_bounce(candles)
        r_grid = test_grid(candles)

        scores = {
            "Simple": r_simple["return"],
            "Bounce": r_bounce["return"],
            "Grid": r_grid["return"],
        }
        best = max(scores, key=scores.get)
        per_asset_best[sym] = best

        print(
            f"{sym:<10} "
            f"{r_simple['return']:>+10.2f}% "
            f"{r_bounce['return']:>+10.2f}% "
            f"{r_grid['return']:>+10.2f}% "
            f"{best:>15}"
        )

    print(f"\n{'='*90}")
    print("📊 خلاصه:")
    print(f"{'='*90}")

    from collections import Counter
    best_counts = Counter(per_asset_best.values())
    for strategy, count in best_counts.most_common():
        assets = [s for s, b in per_asset_best.items() if b == strategy]
        print(f"  {strategy:10}: {count} نماد  →  {', '.join(assets)}")


if __name__ == "__main__":
    asyncio.run(main())
