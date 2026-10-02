"""تست Grid Bot."""

import asyncio
import time

from app.application.use_cases.get_candles import GetCandlesUseCase
from app.core.config import get_settings
from app.infrastructure.exchange.wallex.client import WallexExchange
from app.services.grid_bot import calculate_grid_state, plan_grid

SYMBOLS = ["BTCTMN", "ETHTMN", "XRPTMN", "DOGETMN", "SOLTMN"]
TF = "15m"
N_CANDLES = 2000
INITIAL_CAPITAL = 300_000
FEE_PCT = 0.2
MAX_CONCURRENT_GRIDS = 3
CAPITAL_PER_GRID_PCT = 33.0


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
    capital = INITIAL_CAPITAL
    peak = capital
    max_dd = 0.0
    trades = []

    events = []
    for symbol, candles in markets_data.items():
        for i, c in enumerate(candles):
            events.append((c.time, symbol, i, c))
    events.sort(key=lambda x: x[0])

    # گریدهای فعال
    active_grids = {}  # symbol → GridPlan
    grid_positions = {}  # symbol → GridPosition

    for event_time, symbol, idx, candle in events:
        current_price = float(candle.close)

        # ============ چک گریدهای فعال ============
        if symbol in active_grids:
            plan = active_grids[symbol]
            pos = calculate_grid_state(plan, current_price)

            # آپدیت state
            grid_positions[symbol] = pos

            # چک خروج (میانگین > TP یا قیمت زیر hard SL)
            if pos.filled_levels:  # حداقل یه سطح پر شده
                # TP
                if current_price >= pos.take_profit:
                    pnl_pct = (pos.take_profit / pos.avg_price - 1) * 100 - FEE_PCT
                    pnl_tmn = pos.total_invested * pnl_pct / 100
                    capital += pnl_tmn
                    if capital > peak:
                        peak = capital
                    dd = (peak - capital) / peak * 100
                    if dd > max_dd:
                        max_dd = dd
                    trades.append({"pnl": pnl_pct, "reason": "take_profit", "levels": len(pos.filled_levels)})
                    del active_grids[symbol]
                    del grid_positions[symbol]
                    continue

                # Hard SL
                if current_price <= plan.hard_stop_loss:
                    pnl_pct = (plan.hard_stop_loss / pos.avg_price - 1) * 100 - FEE_PCT
                    pnl_tmn = pos.total_invested * pnl_pct / 100
                    capital += pnl_tmn
                    dd = (peak - capital) / peak * 100
                    if dd > max_dd:
                        max_dd = dd
                    trades.append({"pnl": pnl_pct, "reason": "hard_sl", "levels": len(pos.filled_levels)})
                    del active_grids[symbol]
                    del grid_positions[symbol]
                    continue

            continue  # اگه گرید فعاله، گرید جدید نساز

        # ============ ساخت گرید جدید ============
        if len(active_grids) >= MAX_CONCURRENT_GRIDS:
            continue
        if idx < 50:
            continue

        # capital موجود
        available = capital * (CAPITAL_PER_GRID_PCT / 100)
        if available < 20_000:
            continue

        window = markets_data[symbol][: idx + 1]
        try:
            plan = plan_grid(window, symbol, available)
        except Exception:
            continue

        if plan is None or not plan.should_start:
            continue

        active_grids[symbol] = plan
        grid_positions[symbol] = calculate_grid_state(plan, current_price)

    # بستن گریدهای باز با آخرین قیمت
    for symbol, plan in list(active_grids.items()):
        pos = grid_positions.get(symbol)
        if pos and pos.filled_levels:
            last = markets_data[symbol][-1]
            exit_price = float(last.close)
            pnl_pct = (exit_price / pos.avg_price - 1) * 100 - FEE_PCT
            pnl_tmn = pos.total_invested * pnl_pct / 100
            capital += pnl_tmn
            trades.append({"pnl": pnl_pct, "reason": "end", "levels": len(pos.filled_levels)})

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
    print(f"📊 Grid Bot Backtest")
    print(f"{'='*60}")
    print(f"  بازده:        {result['return_pct']:>+10.2f}%")
    print(f"  سرمایه:       {result['capital']:>11,.0f}")
    print(f"  Max DD:       {result['max_dd']:>11.2f}%")
    print(f"  گریدها:       {result['trades']:>11}")
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
