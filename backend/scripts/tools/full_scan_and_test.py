"""اسکن کامل + تست scalp_master روی همه نمادهای والکس."""

import asyncio
import json
import time
from datetime import datetime, timedelta
from pathlib import Path

from app.application.use_cases.scan_markets import ScanMarketsUseCase
from app.infrastructure.exchange.wallex.client import WallexExchange
from app.infrastructure.wallex_repo import WallexMarketData
from app.core.config import get_settings
from app.services.bot_simulator import BotSimulator

OUTPUT_DIR = Path("data/full_scan")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

RANGE_DAYS = 30
TIMEFRAME = "1h"
INITIAL_BALANCE = 1000.0


async def main():
    settings = get_settings()
    ex = WallexExchange.create(settings)
    
    # ─── مرحله ۱: اسکن همه ───
    print("=" * 70)
    print("مرحله ۱: اسکن همه نمادهای والکس")
    print("=" * 70)
    
    uc = ScanMarketsUseCase(exchange=ex, top_n=400, max_concurrent=20)
    scanned = await uc.execute(quote="TMN", timeframe=TIMEFRAME, min_score=0.0)
    
    print(f"✅ {len(scanned)} نماد اسکن‌شده")
    
    # ذخیره اسکن
    today = datetime.now().strftime("%Y%m%d_%H%M")
    scan_file = OUTPUT_DIR / f"scan_{today}.json"
    scan_data = [
        {
            "symbol": s.symbol,
            "score": s.score.total_score,
            "atr_pct": s.score.atr_pct,
            "std_returns": s.score.std_returns,
            "range_pct": s.score.range_pct,
            "volume_ratio": s.score.volume_ratio,
        }
        for s in scanned
    ]
    scan_file.write_text(json.dumps(scan_data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"💾 {scan_file}")
    
    # ─── مرحله ۲: تست scalp_master ───
    print()
    print("=" * 70)
    print("مرحله ۲: تست scalp_master روی همه نمادها")
    print("=" * 70)
    
    repo = WallexMarketData()
    end = datetime.now()
    start = end - timedelta(days=RANGE_DAYS)
    start_str = start.strftime("%Y-%m-%d")
    end_str = end.strftime("%Y-%m-%d")
    
    results = []
    total = len(scanned)
    
    for i, s in enumerate(scanned, 1):
        symbol = s.symbol
        if i % 20 == 0:
            print(f"[{i}/{total}] {symbol}")
        
        try:
            sim = BotSimulator(repo, "scalp_master", initial_balance=INITIAL_BALANCE)
            r = await sim.run(start_str, end_str, symbol, TIMEFRAME)
            p = r.get("pnl_report", {})
            
            results.append({
                "symbol": symbol,
                "score": s.score.total_score,
                "atr_pct": s.score.atr_pct,
                "trades": p.get("total_trades", 0),
                "pnl_pct": p.get("pnl_pct", 0.0),
                "win_rate": p.get("win_rate", 0.0),
                "status": r.get("status", "error"),
            })
        except Exception as e:
            results.append({
                "symbol": symbol,
                "score": s.score.total_score,
                "atr_pct": s.score.atr_pct,
                "error": str(e)[:100],
            })
        
        # مکث کوتاه
        await asyncio.sleep(0.1)
    
    # ذخیره نتایج
    results_file = OUTPUT_DIR / f"results_{today}.json"
    results_file.write_text(json.dumps(results, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    print(f"\n💾 {results_file}")
    
    # ─── مرحله ۳: خلاصه ───
    print()
    print("=" * 70)
    print("مرحله ۳: خلاصه")
    print("=" * 70)
    
    valid = [r for r in results if r.get("trades", 0) > 0]
    profitable = [r for r in valid if r.get("pnl_pct", 0) > 0]
    
    print(f"کل: {len(results)}")
    print(f"با ترید: {len(valid)}")
    print(f"سودده: {len(profitable)}")
    print()
    
    print("Top 10 سودده:")
    profitable.sort(key=lambda x: x["pnl_pct"], reverse=True)
    for r in profitable[:10]:
        print(f"  {r['symbol']:12s} pnl={r['pnl_pct']:+6.2f}% trades={r['trades']:3d} WR={r['win_rate']:5.1f}% score={r['score']:5.1f}")


if __name__ == "__main__":
    asyncio.run(main())
