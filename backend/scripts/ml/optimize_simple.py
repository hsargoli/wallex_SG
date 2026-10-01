"""بهینه‌سازی Simple Bot — تست ترکیب‌های مختلف."""

import asyncio
from dataclasses import dataclass
from decimal import Decimal

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


def run_config(markets_data, min_score, tp_pct, sl_pct, timeout):
    capital = INITIAL_CAPITAL
    peak = capital
    max_dd = 0.0
    trades = []

    # ساخت رویدادهای زمانی
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

        window = markets_data[symbol][: idx + 1]
        if len(window) < WARMUP:
            continue

        rule = detect_bottom(window)
        if rule.score < min_score:
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


async def main():
    print("📥 دریافت داده...\n")
    markets_data = await fetch_all()
    print(f"✅ {len(markets_data)} نماد\n")

    # ترکیب‌ها
    configs = []

    # ابتدا حول baseline فعلی
    for min_score in [5, 6, 7]:
        for tp in [2.0, 2.5, 3.0]:
            for sl in [1.5]:
                for timeout in [12, 24]:
                    configs.append((min_score, tp, sl, timeout))

    # تست
    print(f"{'='*90}")
    print(f"{'min_score':>10} {'TP':>6} {'SL':>6} {'timeout':>8} {'ترید':>7} {'WR':>8} {'بازده':>10} {'DD':>8}")
    print(f"{'='*90}")

    results = []
    for min_score, tp, sl, timeout in configs:
        r = run_config(markets_data, min_score, tp, sl, timeout)
        results.append({
            "min_score": min_score, "tp": tp, "sl": sl, "timeout": timeout, **r
        })
        print(f"{min_score:>10} {tp:>6.1f} {sl:>6.1f} {timeout:>8} {r['trades']:>7} {r['wr']:>7.1f}% {r['return_pct']:>+9.2f}% {r['max_dd']:>7.2f}%")

    # بهترین‌ها
    print(f"\n{'='*90}")
    print("🏆 بهترین بر اساس بازده:")
    best_return = max(results, key=lambda x: x["return_pct"])
    print(f"   min_score={best_return['min_score']}, TP={best_return['tp']}, SL={best_return['sl']}, timeout={best_return['timeout']}")
    print(f"   بازده: {best_return['return_pct']:+.2f}%  |  ترید: {best_return['trades']}  |  WR: {best_return['wr']:.1f}%  |  DD: {best_return['max_dd']:.2f}%")

    print(f"\n🏆 بهترین بر اساس Win Rate:")
    best_wr = max(results, key=lambda x: x["wr"])
    print(f"   min_score={best_wr['min_score']}, TP={best_wr['tp']}, SL={best_wr['sl']}, timeout={best_wr['timeout']}")
    print(f"   WR: {best_wr['wr']:.1f}%  |  بازده: {best_wr['return_pct']:+.2f}%  |  ترید: {best_wr['trades']}")

    print(f"\n🏆 بهترین بر اساس کمترین DD:")
    best_dd = min(results, key=lambda x: x["max_dd"])
    print(f"   min_score={best_dd['min_score']}, TP={best_dd['tp']}, SL={best_dd['sl']}, timeout={best_dd['timeout']}")
    print(f"   DD: {best_dd['max_dd']:.2f}%  |  بازده: {best_dd['return_pct']:+.2f}%  |  ترید: {best_dd['trades']}")


if __name__ == "__main__":
    asyncio.run(main())
