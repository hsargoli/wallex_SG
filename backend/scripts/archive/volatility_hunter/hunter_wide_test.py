"""تست نوسان‌گیر روی ۲۰ نماد."""

import asyncio

from app.application.use_cases.get_candles import GetCandlesUseCase
from app.core.config import get_settings
from app.infrastructure.exchange.wallex.client import WallexExchange
from app.services.bots.volatility_hunter.config import VolatilityHunterConfig
from app.services.bots.volatility_hunter.strategy import evaluate_entry, evaluate_exit

# ۲۰ نماد متنوع
SYMBOLS = [
    # Major
    "BTCTMN", "ETHTMN", "XRPTMN", "SOLTMN",
    # Mid-cap
    "BNBTMN", "ADATMN", "LINKTMN", "DOGETMN",
    "DASHTMN", "LTCTMN", "TRXTMN",
    # Small-cap
    "ZECTMN", "GRAMTMN", "HBARTMN", "UNITMN",
    "GALATM", "CELRTMN", "ONETMN", "BTTC TMN".replace(" ", ""), "ONE TMN".replace(" ", ""),
]
SYMBOLS = list(dict.fromkeys(SYMBOLS))  # unique

TF = "1h"
N_CANDLES = 2000
INITIAL_CAPITAL = 300_000
FEE_PCT = 0.2
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


def run_backtest(markets_data, config):
    capital = INITIAL_CAPITAL
    peak = capital
    max_dd = 0
    trades = []
    open_positions = {}

    events = []
    for sym, candles in markets_data.items():
        for i, c in enumerate(candles):
            events.append((c.time, sym, i, c))
    events.sort(key=lambda x: x[0])

    for _, sym, idx, candle in events:
        if sym in open_positions:
            pos = open_positions[sym]
            window = markets_data[sym][: idx + 1]
            should_exit, exit_p, reason = evaluate_exit(
                window, pos["entry"], pos["sl"], pos["tp"], config,
            )
            if should_exit:
                pnl = (exit_p / pos["entry"] - 1) * 100 - FEE_PCT
                capital += pos["invest"] * pnl / 100
                if capital > peak: peak = capital
                dd = (peak - capital) / peak * 100
                if dd > max_dd: max_dd = dd
                trades.append({"pnl": pnl, "reason": reason, "symbol": sym})
                del open_positions[sym]

        if len(open_positions) >= MAX_POSITIONS or sym in open_positions:
            continue
        if idx < config.warmup_candles:
            continue

        window = markets_data[sym][: idx + 1]
        sig = evaluate_entry(window, config)
        if sig is None: continue

        invest = capital * (config.position_size_pct / 100)
        if invest < 5000: continue

        open_positions[sym] = {
            "entry": sig.entry_price, "sl": sig.stop_loss,
            "tp": sig.take_profit, "invest": invest,
        }

    for sym, pos in open_positions.items():
        last = markets_data[sym][-1]
        pnl = (float(last.close) / pos["entry"] - 1) * 100 - FEE_PCT
        capital += pos["invest"] * pnl / 100
        trades.append({"pnl": pnl, "reason": "end", "symbol": sym})

    wins = sum(1 for t in trades if t["pnl"] > 0)
    wr = wins / len(trades) * 100 if trades else 0
    ret = (capital / INITIAL_CAPITAL - 1) * 100
    rdd = ret / max_dd if max_dd > 0 else 0

    return {
        "return": ret, "trades": len(trades), "wins": wins,
        "losses": len(trades) - wins, "wr": wr, "dd": max_dd, "rdd": rdd,
        "trade_list": trades,
    }


async def main():
    print(f"📥 دریافت {len(SYMBOLS)} نماد...\n")
    data = await fetch_all()
    print(f"✅ {len(data)} نماد\n")

    config = VolatilityHunterConfig()
    result = run_backtest(data, config)

    print(f"{'='*60}")
    print(f"📊 Volatility Hunter — Wide Test")
    print(f"{'='*60}")
    print(f"  نمادها:       {len(data)}")
    print(f"  بازده:        {result['return']:>+9.2f}%")
    print(f"  ترید:         {result['trades']}")
    print(f"  برد/باخت:     {result['wins']} / {result['losses']}")
    print(f"  WR:           {result['wr']:>8.1f}%")
    print(f"  Max DD:       {result['dd']:>8.2f}%")
    print(f"  R/DD:         {result['rdd']:>8.2f}")

    # per-symbol breakdown
    print(f"\n  📊 per-symbol breakdown:")
    sym_stats = {}
    for t in result["trade_list"]:
        s = t["symbol"]
        if s not in sym_stats:
            sym_stats[s] = {"trades": 0, "wins": 0, "total_pnl": 0}
        sym_stats[s]["trades"] += 1
        if t["pnl"] > 0:
            sym_stats[s]["wins"] += 1
        sym_stats[s]["total_pnl"] += t["pnl"]

    sorted_syms = sorted(sym_stats.items(), key=lambda x: -x[1]["total_pnl"])
    print(f"  {'symbol':<12} {'ترید':>5} {'WR':>6} {'pnl%':>8}")
    for sym, st in sorted_syms:
        wr = st["wins"] / st["trades"] * 100 if st["trades"] else 0
        emoji = "🟢" if st["total_pnl"] > 0 else "🔴"
        print(f"  {emoji} {sym:<10} {st['trades']:>5} {wr:>5.1f}% {st['total_pnl']:>+7.2f}%")


if __name__ == "__main__":
    asyncio.run(main())
