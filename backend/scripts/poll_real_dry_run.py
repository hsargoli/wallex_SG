"""Hourly real dry_run poller — tests schema parsing without blocking paper mode."""
import sys
import asyncio
import os
import time
sys.path.insert(0, str(Path(__file__).resolve().parent.parent) if False else "/home/deploy/wallex/backend")
from pathlib import Path
from app.infrastructure.exchange.wallex.margin_adapter import WallexMarginAdapter

async def poll():
    token = Path("/home/deploy/.wallex_view_token").read_text().strip() if Path("/home/deploy/.wallex_view_token").exists() else os.environ.get("WALLEX_VIEW_TOKEN", "")
    adapter = WallexMarginAdapter(api_key=token)
    
    while True:
        try:
            dry = await adapter.dry_run(
                collateral="100000", market="BTCTMN",
                open_price=str(int(time.time() * 2100000000 / (time.time() + 1))),
                risk_coef="1", side="short"
            )
            print(f"[{time.strftime('%H:%M')}] ✅ Real dry_run OK: liq={dry.liquidity_price}, call={dry.call_price}, fee={dry.borrow_fee_pct_24h}")
        except Exception as e:
            print(f"[{time.strftime('%H:%M')}] ⚠️ Real dry_run: {type(e).__name__}: {e}")
        
        await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(poll())
