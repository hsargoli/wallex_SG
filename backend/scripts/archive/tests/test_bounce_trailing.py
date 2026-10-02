"""تست Bounce Scalper با Trailing Stop."""

import asyncio
import time

from app.application.use_cases.get_candles import GetCandlesUseCase
from app.core.config import get_settings
from app.infrastructure.exchange.wallex.client import WallexExchange
from app.services.bounce_scalper import (
    check_bounce_exit_trailing, make_bounce_decision,
)
from app.services.indicators import atr

SYMBOLS = ["BTCTMN", "ETHTMN", "XRPTMN", "DOGETMN", "SOLTMN"]
TF = "15m"
N_CANDLES = 2000
INITIAL_CAPITAL = 300_000
FEE_PCT = 0.2
MAX_POSITIONS = 3
POSITION_SIZE_PCT = 33.0


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


def _last(values):
    for v in reversed(values):
        if v is not None:
            return v
    return None


def run_backtest(markets_data):
    capital = INITIAL_CAPITAL
    peak = capital
    max_dd = 0.0
    trades = []

    # پیش‌محاسبه ATR برای هر نماد
    atr_cache = {}
    for symbol, candles in markets_data.items():
        atr_cache[symbol] = atr(candles, 14)

    events = []
    for symbol, candles in markets_data.items():
        for i, c in enumerate(candles):
            events.append((c.time, symbol, i, c))
    events.sort(key=lambda x: x[0])

    open_positions = {}

    for event_time, symbol, idx, candle in events:
        if symbol in open_positions:
            pos = open_positions[symbol]
            atr_val = atr_cache[symbol][pos["entry_idx"]] or 0
            atr_float = float(atr_val) if atr_val else pos["entry"] * 0.005

            should_exit, exit_price, reason, new_sl = check_bounce_exit_trailing(
                pos["entry"], pos["tp"], pos["sl"],
                atr_float, pos["current_sl"],
                candle, idx - pos["entry_idx"],
            )

            # آپدیت SL (trailing)
            if new_sl > pos["current_sl"]:
                pos["current_sl"] = new_sl

            if should_exit:
                pnl_pct = (exit_price / pos["entry"] - 1) * 100 - FEE_PCT
                pnl_tmn = pos["invest"] * pnl_pct / 100
                capital += pnl_tmn
                if capital > peak:
                    peak = capital
                dd = (peak - capital) / peak * 100
                if dd > max_dd:
                    max_dd = dd
                trades.append({"pnl": pnl_pct, "reason": reason})
                del open_positions[symbol]

        if len(open_positions) >= MAX_POSITIONS:
            continue
        if symbol in open_positions:
            continue
        if idx < 30:
            continue

        window = markets_data[symbol][: idx + 1]
        try:
            decision = make_bounce_decision(window)
        except Exception:
            continue

        if not decision.should_trade:
            continue

        invest = capital * (POSITION_SIZE_PCT / 100)
        invest = min(invest, capital * 0.95)
        if invest < 5_000:
            continue

        open_positions[symbol] = {
            "entry": decision.entry_price,
            "tp": decision.take_profit,
            "sl": decision.stop_loss,
            "current_sl": decision.stop_loss,
            "invest": invest,
            "entry_idx": idx,
        }

    # بستن بازها
    for symbol, pos in open_positions.items():
        last = markets_data[symbol][-1]
        exit_price = float(last.close)
        pnl_pct = (exit_price / pos["entry"] - 1) * 100 - FEE_PCT
        pnl_tmn = pos["invest"] * pnl_pct / 100
        capital += pnl_tmn
        trades.append({"pnl": pnl_pct, "reason": "end"})

    wins = sum(1 for t in trades if t["pnl"] > 0)
    wr = wins / len(trades) * 100 if trades else 0

    reasons = {}
    for t in trades:
        reasons[t["reason"]] = reasons.get(t["reason"], 0) + 1

    wins_list = [t["pnl"] for t in trades if t["pnl"] > 0]
    losses_list = [t["pnl"] for t in trades if t["pnl"] <= 0]

    avg_win = sum(wins_list) / len(wins_list) if wins_list else 0
    avg_loss = sum(losses_list) / len(losses_list) if losses_list else 0
    rr = abs(avg_win / avg_loss) if avg_loss != 0 else 0

    return {
        "capital": capital,
        "return_pct": (capital / INITIAL_CAPITAL - 1) * 100,
        "trades": len(trades),
        "wins": wins,
        "losses": len(trades) - wins,
        "wr": wr,
        "max_dd": max_dd,
        "reasons": reasons,
        "avg_win": avg_win,
        "avg_loss": avg_loss,
        "rr": rr,
    }


async def main():
    print("📥 دریافت داده...\n")
    markets_data = await fetch_all()
    print(f"✅ {len(markets_data)} نماد، {sum(len(c) for c in markets_data.values())} کندل\n")

    start = time.time()
    result = run_backtest(markets_data)

    print(f"{'='*60}")
    print(f"📊 Bounce Scalper v3 (Trailing Stop)")
    print(f"{'='*60}")
    print(f"  بازده:        {result['return_pct']:>+10.2f}%")
    print(f"  سرمایه:       {result['capital']:>11,.0f}")
    print(f"  Max DD:       {result['max_dd']:>11.2f}%")
    print(f"  ترید:         {result['trades']:>11}")
    print(f"  برد/باخت:     {result['wins']:>5} / {result['losses']}")
    print(f"  WR:           {result['wr']:>11.1f}%")
    print(f"\n  📈 میانگین سود:  {result['avg_win']:>+10.3f}%")
    print(f"  📉 میانگین ضرر:  {result['avg_loss']:>+10.3f}%")
    print(f"  🎯 R/R واقعی:    {result['rr']:>11.2f}")
    print(f"\n  دلایل خروج:")
    for r, c in sorted(result['reasons'].items(), key=lambda x: -x[1]):
        pct = c / result['trades'] * 100
        print(f"    {r:12}: {c:>4}  ({pct:>5.1f}%)")
    print(f"\n  ⏱️  {time.time()-start:.1f}s")


if __name__ == "__main__":
    asyncio.run(main())
