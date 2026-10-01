"""Backtest روندرو."""

import asyncio
import time

from app.application.use_cases.get_candles import GetCandlesUseCase
from app.core.config import get_settings
from app.infrastructure.exchange.wallex.client import WallexExchange
from app.services.bots.trend_follow.config import TrendFollowConfig
from app.services.bots.trend_follow.strategy import evaluate_entry, evaluate_exit

SYMBOLS = ["BTCTMN", "ETHTMN", "XRPTMN", "SOLTMN", "BNBTMN", "ADATMN", "LINKTMN", "HBARTMN", "DASHTMN", "TRXTMN", "LTCTMN", "UNITMN", "ZECTMN", "GRAMTMN"]
TF = "1h"
N_CANDLES = 2000
INITIAL_CAPITAL = 300_000
FEE_PCT = 0.2
POSITION_SIZE_PCT = 30.0
MAX_POSITIONS = 3


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


def run_backtest(markets_data):
    config = TrendFollowConfig()
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
            window = markets_data[symbol][: idx + 1]
            exit_res = evaluate_exit(
                window, pos["entry"], pos["current_sl"],
                pos["trailing_distance"], config,
                idx - pos["entry_idx"],
            )
            if exit_res.new_sl and exit_res.new_sl > pos["current_sl"]:
                pos["current_sl"] = exit_res.new_sl
            if exit_res.should_exit:
                exit_price = float(candle.close) if exit_res.reason in ("timeout", "reverse_cross") else pos["current_sl"]
                pnl = (exit_price / pos["entry"] - 1) * 100 - FEE_PCT
                capital += pos["invest"] * pnl / 100
                if capital > peak: peak = capital
                dd = (peak - capital) / peak * 100
                if dd > max_dd: max_dd = dd
                trades.append({"pnl": pnl, "reason": exit_res.reason})
                del open_positions[symbol]

        # ورود
        if len(open_positions) >= MAX_POSITIONS:
            continue
        if symbol in open_positions:
            continue
        if idx < config.warmup_candles:
            continue

        window = markets_data[symbol][: idx + 1]
        signal = evaluate_entry(window, config)
        if signal is None:
            continue

        invest = capital * (POSITION_SIZE_PCT / 100)
        if invest < 5000: continue

        open_positions[symbol] = {
            "entry": signal.entry_price,
            "current_sl": signal.initial_sl,
            "trailing_distance": signal.trailing_distance,
            "invest": invest,
            "entry_idx": idx,
        }

    # بستن بازها
    for symbol, pos in open_positions.items():
        last = markets_data[symbol][-1]
        exit_price = float(last.close)
        pnl = (exit_price / pos["entry"] - 1) * 100 - FEE_PCT
        capital += pos["invest"] * pnl / 100
        trades.append({"pnl": pnl, "reason": "end"})

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
        "avg_win": avg_win,
        "avg_loss": avg_loss,
        "rr": rr,
        "reasons": reasons,
    }


async def main():
    print(f"📥 دریافت {len(SYMBOLS)} نماد ({TF})...\n")
    markets_data = await fetch_all()
    print(f"✅ {len(markets_data)} نماد\n")

    start = time.time()
    result = run_backtest(markets_data)

    print(f"{'='*60}")
    print(f"📊 Trend Follow Backtest")
    print(f"{'='*60}")
    print(f"  بازده:        {result['return_pct']:>+10.2f}%")
    print(f"  سرمایه:       {result['capital']:>11,.0f}")
    print(f"  Max DD:       {result['max_dd']:>11.2f}%")
    print(f"  ترید:         {result['trades']:>11}")
    print(f"  برد/باخت:     {result['wins']:>5} / {result['losses']}")
    print(f"  WR:           {result['wr']:>11.1f}%")
    print(f"  میانگین سود:  {result['avg_win']:>+10.3f}%")
    print(f"  میانگین ضرر:  {result['avg_loss']:>+10.3f}%")
    print(f"  R/R:          {result['rr']:>11.2f}")
    print(f"\n  دلایل خروج:")
    for r, c in sorted(result['reasons'].items(), key=lambda x: -x[1]):
        print(f"    {r:15}: {c:>4}")
    print(f"\n  ⏱️  {time.time()-start:.1f}s")


if __name__ == "__main__":
    asyncio.run(main())
