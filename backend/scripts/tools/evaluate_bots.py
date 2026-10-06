"""ارزیاب ربات‌ها — تست همه ترکیب‌ها.

۴ ربات × ۳ TF × ۳ بازه × ۳ نماد
"""

import asyncio
import json
from datetime import datetime, timedelta
from pathlib import Path

from app.services.bot_simulator import BotSimulator, list_simulatable_bots
from app.infrastructure.wallex_repo import WallexMarketData


SLUGS = list_simulatable_bots()
TIMEFRAMES = ["1h", "4h", "1D"]
RANGE_DAYS = [30, 90, 180]
SYMBOLS = ["BTCUSDT", "ETHUSDT", "ADAUSDT"]

OUTPUT_DIR = Path("data/backtest_results")


async def run_one(repo, slug, symbol, days, timeframe):
    end = datetime.now()
    start = end - timedelta(days=days)
    start_str = start.strftime("%Y-%m-%d")
    end_str = end.strftime("%Y-%m-%d")
    
    try:
        sim = BotSimulator(repo, slug, initial_balance=1000.0)
        r = await sim.run(start_str, end_str, symbol, timeframe)
        p = r.get("pnl_report", {})
        return {
            "slug": slug,
            "symbol": symbol,
            "days": days,
            "timeframe": timeframe,
            "status": r.get("status"),
            "trades": p.get("total_trades", 0),
            "pnl_pct": p.get("pnl_pct", 0.0),
            "win_rate": p.get("win_rate", 0.0),
            "final_balance": p.get("final_balance", 0.0),
            "error": r.get("message", "")[:100] if r.get("status") == "error" else "",
        }
    except Exception as e:
        return {
            "slug": slug, "symbol": symbol, "days": days, "timeframe": timeframe,
            "status": "exception", "error": str(e)[:100],
        }


async def main():
    repo = WallexMarketData()
    results = []
    total = len(SLUGS) * len(TIMEFRAMES) * len(RANGE_DAYS) * len(SYMBOLS)
    i = 0
    
    for symbol in SYMBOLS:
        for timeframe in TIMEFRAMES:
            for days in RANGE_DAYS:
                for slug in SLUGS:
                    i += 1
                    print(f"[{i}/{total}] {symbol} {timeframe} {days}d {slug}")
                    r = await run_one(repo, slug, symbol, days, timeframe)
                    results.append(r)
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    today = datetime.now().strftime("%Y%m%d")
    out = OUTPUT_DIR / f"evaluate_{today}.json"
    out.write_text(json.dumps(results, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    print(f"\n✅ {len(results)} نتیجه ذخیره شد: {out}")


if __name__ == "__main__":
    asyncio.run(main())
