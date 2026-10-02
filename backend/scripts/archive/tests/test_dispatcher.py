"""تست Dispatcher — ببینیم با استراتژی per-asset چقدر سود می‌ده."""

import asyncio
import time

from app.application.use_cases.get_candles import GetCandlesUseCase
from app.core.config import get_settings
from app.infrastructure.exchange.wallex.client import WallexExchange
from app.services.smart_dispatcher import dispatcher

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


def run_dispatcher_backtest(markets_data):
    from app.services.bounce_scalper import check_bounce_exit
    from app.services.simple_bot import check_simple_exit

    capital = INITIAL_CAPITAL
    peak = capital
    max_dd = 0.0
    trades = []
    per_strategy = {"simple": [], "bounce": []}

    events = []
    for symbol, candles in markets_data.items():
        for i, c in enumerate(candles):
            events.append((c.time, symbol, i, c))
    events.sort(key=lambda x: x[0])

    open_positions = {}
    skipped_symbols = set()

    for event_time, symbol, idx, candle in events:
        # چک خروج
        if symbol in open_positions:
            pos = open_positions[symbol]

            # بر اساس استراتژی، check_exit مناسب
            if pos["strategy"] == "simple":
                should_exit, exit_price, reason = check_simple_exit(
                    pos["entry"], pos["tp"], pos["sl"],
                    candle, idx - pos["entry_idx"],
                )
            else:  # bounce
                should_exit, exit_price, reason = check_bounce_exit(
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
                trades.append({"pnl": pnl_pct, "strategy": pos["strategy"]})
                per_strategy[pos["strategy"]].append(pnl_pct)
                del open_positions[symbol]

        # چک ورود
        if len(open_positions) >= MAX_POSITIONS:
            continue
        if symbol in open_positions:
            continue
        if idx < 50:
            continue

        # اگه نماد استراتژی نداره، skip کن
        if symbol not in dispatcher.list_active():
            skipped_symbols.add(symbol)
            continue

        window = markets_data[symbol][: idx + 1]
        try:
            decision = dispatcher.make_decision(symbol, window)
        except Exception:
            continue

        if decision is None or not decision["should_trade"]:
            continue

        invest = capital * (POSITION_SIZE_PCT / 100)
        invest = min(invest, capital * 0.95)
        if invest < 5_000:
            continue

        open_positions[symbol] = {
            "entry": decision["entry"],
            "tp": decision["tp"],
            "sl": decision["sl"],
            "strategy": decision["strategy"],
            "invest": invest,
            "entry_idx": idx,
        }

    # بستن پوزیشن‌های باز
    for symbol, pos in open_positions.items():
        last = markets_data[symbol][-1]
        exit_price = float(last.close)
        pnl_pct = (exit_price / pos["entry"] - 1) * 100 - FEE_PCT
        pnl_tmn = pos["invest"] * pnl_pct / 100
        capital += pnl_tmn
        trades.append({"pnl": pnl_pct, "strategy": pos["strategy"]})

    # آمار
    wins = sum(1 for t in trades if t["pnl"] > 0)
    wr = wins / len(trades) * 100 if trades else 0

    wins_list = [t["pnl"] for t in trades if t["pnl"] > 0]
    losses_list = [t["pnl"] for t in trades if t["pnl"] <= 0]
    avg_win = sum(wins_list) / len(wins_list) if wins_list else 0
    avg_loss = sum(losses_list) / len(losses_list) if losses_list else 0
    rr = abs(avg_win / avg_loss) if avg_loss != 0 else 0

    # آمار per-strategy
    strat_stats = {}
    for strat, pnls in per_strategy.items():
        if pnls:
            w = sum(1 for p in pnls if p > 0)
            strat_stats[strat] = {
                "trades": len(pnls),
                "wr": w / len(pnls) * 100,
                "avg": sum(pnls) / len(pnls),
            }

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
        "strat_stats": strat_stats,
        "skipped": list(skipped_symbols),
    }


async def main():
    print(f"📥 دریافت {len(SYMBOLS)} نماد...\n")
    markets_data = await fetch_all()
    print(f"✅ {len(markets_data)} نماد\n")

    start = time.time()
    result = run_dispatcher_backtest(markets_data)

    print(f"{'='*70}")
    print(f"📊 Smart Dispatcher Backtest")
    print(f"{'='*70}")
    print(f"  بازده:        {result['return_pct']:>+10.2f}%")
    print(f"  سرمایه:       {result['capital']:>11,.0f}")
    print(f"  Max DD:       {result['max_dd']:>11.2f}%")
    print(f"  ترید:         {result['trades']:>11}")
    print(f"  برد/باخت:     {result['wins']:>5} / {result['losses']}")
    print(f"  WR:           {result['wr']:>11.1f}%")
    print(f"  میانگین سود:  {result['avg_win']:>+10.3f}%")
    print(f"  میانگین ضرر:  {result['avg_loss']:>+10.3f}%")
    print(f"  R/R:          {result['rr']:>11.2f}")

    print(f"\n  📊 per-strategy:")
    for strat, stats in result["strat_stats"].items():
        print(f"    {strat:10}: {stats['trades']:>4} ترید  |  WR={stats['wr']:>5.1f}%  |  avg={stats['avg']:+.3f}%")

    print(f"\n  ⏱️  {time.time()-start:.1f}s")


if __name__ == "__main__":
    asyncio.run(main())
