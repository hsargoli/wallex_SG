"""
تست نقدینگی مارجین روی چند market.
هدف: بفهمیم والکس روی کدوم جفت‌ارزها ظرفیت وام دادن داره.
SAFETY: فقط dry_run — هیچ پوزیشن واقعی باز نمی‌شه.
"""
import asyncio
import json
from getpass import getpass
import httpx

BASE = "https://api.wallex.ir"

MARKETS = ["BTCTMN", "ETHTMN", "XRPTMN", "ADATMN", "DOGETMN", "TRXTMN", "SOLTMN", "BNBTMN", "LINKTMN", "DOTTMN"]
SIZES = ["10000", "50000", "100000"]

async def test_one(client, headers, market, size, open_price):
    payload = {
        "collateral": size, "market": market, "open_price": open_price,
        "risk_coef": "1", "side": "short",
        "stop_loss": str(int(float(open_price) * 1.03)),
        "take_profit": str(int(float(open_price) * 0.955)),
    }
    try:
        resp = await client.post(f"{BASE}/margin-trade/v1/public/dry-run", json=payload, headers=headers)
        if resp.status_code == 200:
            return ("OK", resp.json().get("result", {}))
        if resp.status_code == 400:
            msg = resp.json().get("message", "")
            if "ظرفیت" in msg:
                return ("NO_LIQ", msg)
            return ("400", msg)
        return (str(resp.status_code), resp.text[:100])
    except Exception as e:
        return ("ERR", f"{type(e).__name__}: {e}")

async def main():
    print("=" * 70)
    print("🔍 Wallex Margin Liquidity Test")
    print("=" * 70)
    token = getpass("View token (hidden): ").strip()
    if not token:
        return
    headers = {"x-api-key": token, "Accept": "application/json", "Content-Type": "application/json"}

    async with httpx.AsyncClient(timeout=20) as client:
        # 1. Get current prices for all markets
        r = await client.get(f"{BASE}/v1/markets")
        all_markets = r.json().get("result", {}).get("symbols", {})
        
        results = {}
        for market in MARKETS:
            if market not in all_markets:
                print(f"\n⚠️  {market}: not found in markets")
                continue
            price = all_markets[market].get("stats", {}).get("lastPrice", 0)
            if not price:
                print(f"\n⚠️  {market}: no price")
                continue
            open_price = str(price)
            print(f"\n{'─'*60}")
            print(f"🪙 {market} @ {open_price}")
            for size in SIZES:
                status, data = await test_one(client, headers, market, size, open_price)
                if status == "OK":
                    print(f"   ✅ {size:>7} TMN → OK (liq_price={data.get('liquidity_price', 'N/A')})")
                elif status == "NO_LIQ":
                    print(f"   ❌ {size:>7} TMN → NO_LIQUIDITY")
                else:
                    print(f"   ⚠️  {size:>7} TMN → {status}: {data[:80]}")
                results[f"{market}_{size}"] = status

    print("\n" + "=" * 70)
    print("📊 Summary")
    print("=" * 70)
    available = [k for k, v in results.items() if v == "OK"]
    print(f"Available combinations: {len(available)} / {len(results)}")
    for k in available:
        print(f"  ✅ {k}")

if __name__ == "__main__":
    asyncio.run(main())
