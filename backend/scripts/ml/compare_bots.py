"""مقایسه‌ی ۳ ربات روی داده‌ی مشترک.

هدف: ببینیم هر ربات در کدوم رژیم بازار بهتره.
"""

import asyncio
import time

from app.application.use_cases.get_candles import GetCandlesUseCase
from app.core.config import get_settings
from app.infrastructure.exchange.wallex.client import WallexExchange
from app.services.bots.grid_bot.config import GridBotConfig
from app.services.bots.grid_bot.strategy import should_start_grid
from app.services.bots.mean_revert import MeanRevertConfig
from app.services.bots.trend_follow.config import TrendFollowConfig
from app.services.bots.trend_follow.strategy import evaluate_entry as tf_entry, evaluate_exit as tf_exit

SYMBOLS = ["BTCTMN", "ETHTMN", "XRPTMN", "SOLTMN", "BNBTMN", "ADATMN", "LINKTMN", "HBARTMN"]
INITIAL_CAPITAL = 300_000
FEE_PCT = 0.2


async def fetch_all(tf):
    settings = get_settings()
    async def one(sym):
        ex = WallexExchange.create(settings)
        try:
            uc = GetCandlesUseCase(exchange=ex)
            return sym, await uc.execute(symbol=sym, timeframe=tf, limit=2000)
        except Exception:
            return sym, []
        finally:
            await ex.aclose()
    results = await asyncio.gather(*[one(s) for s in SYMBOLS])
    return {s: c for s, c in results if c}


def _last(v):
    for x in reversed(v):
        if x is not None:
            return x
    return None


# ============ Mean Revert ============
def test_mean_revert(markets_data):
    from app.services.bottom_detector import detect_bottom
    from app.services.indicators import ema

    capital = INITIAL_CAPITAL
    peak = capital
    dd_max = 0
    trades = []

    for symbol, candles in markets_data.items():
        open_pos = None
        for idx in range(50, len(candles)):
            candle = candles[idx]

            if open_pos:
                if candle.high >= open_pos["tp"] or candle.low <= open_pos["sl"] or idx - open_pos["idx"] >= 12:
                    if candle.high >= open_pos["tp"]:
                        exit_p = open_pos["tp"]
                    elif candle.low <= open_pos["sl"]:
                        exit_p = open_pos["sl"]
                    else:
                        exit_p = float(candle.close)
                    pnl = (exit_p / open_pos["entry"] - 1) * 100 - FEE_PCT
                    capital += open_pos["invest"] * pnl / 100
                    if capital > peak: peak = capital
                    dd = (peak - capital) / peak * 100
                    if dd > dd_max: dd_max = dd
                    trades.append(pnl)
                    open_pos = None
                continue

            window = candles[:idx+1]
            try:
                rule = detect_bottom(window)
            except Exception:
                continue
            if rule.score < 6:
                continue

            e20 = _last(ema(window, 20))
            e50 = _last(ema(window, 50))
            if e20 and e50 and e20 < e50:
                continue

            entry = float(candle.close)
            invest = capital * 0.3
            if invest < 5000: continue

            open_pos = {"entry": entry, "tp": entry*1.02, "sl": entry*0.985, "invest": invest, "idx": idx}

    wins = sum(1 for t in trades if t > 0)
    return {
        "return": (capital/INITIAL_CAPITAL-1)*100,
        "trades": len(trades), "wins": wins, "losses": len(trades)-wins,
        "wr": wins/len(trades)*100 if trades else 0,
        "dd": dd_max, "capital": capital,
    }


# ============ Trend Follow ============
def test_trend_follow(markets_data):
    config = TrendFollowConfig()
    capital = INITIAL_CAPITAL
    peak = capital
    dd_max = 0
    trades = []
    positions = {}

    events = []
    for sym, candles in markets_data.items():
        for i, c in enumerate(candles):
            events.append((c.time, sym, i, c))
    events.sort(key=lambda x: x[0])

    for _, sym, idx, candle in events:
        # Exit
        if sym in positions:
            pos = positions[sym]
            window = markets_data[sym][:idx+1]
            ex = tf_exit(window, pos["entry"], pos["sl"], pos["trail"], config, idx - pos["idx"])
            if ex.new_sl and ex.new_sl > pos["sl"]:
                pos["sl"] = ex.new_sl
            if ex.should_exit:
                exit_p = float(candle.close) if ex.reason in ("timeout", "reverse_cross") else pos["sl"]
                pnl = (exit_p / pos["entry"] - 1) * 100 - FEE_PCT
                capital += pos["invest"] * pnl / 100
                if capital > peak: peak = capital
                dd = (peak-capital)/peak*100
                if dd > dd_max: dd_max = dd
                trades.append(pnl)
                del positions[sym]

        # Entry
        if len(positions) >= 3 or sym in positions or idx < config.warmup_candles:
            continue
        window = markets_data[sym][:idx+1]
        try:
            sig = tf_entry(window, config)
        except Exception:
            continue
        if sig is None: continue

        invest = capital * 0.3
        if invest < 5000: continue
        positions[sym] = {"entry": sig.entry_price, "sl": sig.initial_sl,
                          "trail": sig.trailing_distance, "invest": invest, "idx": idx}

    for sym, pos in positions.items():
        last = markets_data[sym][-1]
        pnl = (float(last.close)/pos["entry"]-1)*100 - FEE_PCT
        capital += pos["invest"]*pnl/100
        trades.append(pnl)

    wins = sum(1 for t in trades if t > 0)
    return {
        "return": (capital/INITIAL_CAPITAL-1)*100,
        "trades": len(trades), "wins": wins, "losses": len(trades)-wins,
        "wr": wins/len(trades)*100 if trades else 0,
        "dd": dd_max, "capital": capital,
    }


# ============ Grid Bot (ساده) ============
def test_grid_bot(markets_data):
    """نسخه‌ی ساده‌ی grid برای تست."""
    config = GridBotConfig()
    capital = INITIAL_CAPITAL
    peak = capital
    dd_max = 0
    trades = []

    for sym, candles in markets_data.items():
        # شبیه‌سازی grid کوچیک
        for idx in range(50, len(candles)):
            candle = candles[idx]
            window = candles[:idx+1]
            try:
                sig = should_start_grid(window, sym, capital, config)
            except Exception:
                continue
            if not sig.should_start or sig.plan is None:
                continue

            # بررسی سریع سود/ضرر با این plan
            plan = sig.plan
            # فرض: اولین buy level پر می‌شه و به سود می‌رسه اگه قیمت برگرده
            buy_level = next((l for l in plan.levels if l.level_type == "buy"), None)
            if buy_level is None:
                continue

            # بررسی 30 کندل بعدی
            future = candles[idx+1:idx+30]
            if not future:
                continue

            entry = buy_level.price
            max_high = max(float(c.high) for c in future)
            min_low = min(float(c.low) for c in future)

            target = entry * 1.008  # 0.8% سود
            stop = entry * 0.99     # 1% حد ضرر

            if min_low <= stop and max_high < target:
                pnl = -1.0 - FEE_PCT
                trades.append(pnl)
                capital += capital * 0.15 * pnl / 100
            elif max_high >= target:
                pnl = 0.8 - FEE_PCT
                trades.append(pnl)
                capital += capital * 0.15 * pnl / 100
            else:
                pnl = (float(future[-1].close)/entry-1)*100 - FEE_PCT
                trades.append(pnl)
                capital += capital * 0.15 * pnl / 100

            if capital > peak: peak = capital
            dd = (peak-capital)/peak*100
            if dd > dd_max: dd_max = dd

    wins = sum(1 for t in trades if t > 0)
    return {
        "return": (capital/INITIAL_CAPITAL-1)*100,
        "trades": len(trades), "wins": wins, "losses": len(trades)-wins,
        "wr": wins/len(trades)*100 if trades else 0,
        "dd": dd_max, "capital": capital,
    }


def print_result(name, r):
    print(f"\n  📊 {name}")
    print(f"     بازده:     {r['return']:>+9.2f}%")
    print(f"     ترید:      {r['trades']:>9}")
    print(f"     WR:        {r['wr']:>8.1f}%")
    print(f"     Max DD:    {r['dd']:>8.2f}%")
    if r['dd'] > 0:
        print(f"     بازده/DD:  {r['return']/r['dd']:>8.2f}")


async def main():
    for tf in ["15m", "1h", "4h"]:
        print(f"\n{'='*70}")
        print(f"🎯 تایم‌فریم: {tf}")
        print(f"{'='*70}")

        markets_data = await fetch_all(tf)
        if len(markets_data) < 3:
            print(f"  ❌ فقط {len(markets_data)} نماد")
            continue

        total_candles = sum(len(c) for c in markets_data.values())
        print(f"  ✅ {len(markets_data)} نماد، {total_candles} کندل")

        start = time.time()
        r1 = test_mean_revert(markets_data)
        r2 = test_trend_follow(markets_data)
        r3 = test_grid_bot(markets_data)

        print_result("کف‌زن (mean_revert)", r1)
        print_result("روندرو (trend_follow)", r2)
        print_result("شبکه‌ای (grid_bot)", r3)

        # برنده
        scores = {
            "کف‌زن": r1["return"],
            "روندرو": r2["return"],
            "شبکه‌ای": r3["return"],
        }
        best = max(scores, key=scores.get)
        print(f"\n  🏆 برنده در {tf}: {best} با {scores[best]:+.2f}%")
        print(f"\n  ⏱️  {time.time()-start:.1f}s")


if __name__ == "__main__":
    asyncio.run(main())
