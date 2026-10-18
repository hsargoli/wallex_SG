"""
Debug: Print RAW JSON + headers from Wallex API.
No parsing. Just the truth.
"""
import asyncio
import json
import httpx
from getpass import getpass

BASE = "https://api.wallex.ir"

async def debug_endpoint(client, name, method, path, **kwargs):
    print(f"\n{'='*60}")
    print(f"🔍 {name}: {method} {path}")
    print(f"{'='*60}")
    print(f"Request kwargs: {json.dumps(kwargs, default=str)}")
    try:
        resp = await client.request(method, f"{BASE}{path}", **kwargs)
        print(f"Status: {resp.status_code}")
        print(f"Content-Type: {resp.headers.get('content-type')}")
        print(f"Body (first 2000 chars):")
        print(resp.text[:2000])
        return resp
    except Exception as e:
        print(f"❌ Exception: {type(e).__name__}: {e}")
        return None

async def main():
    print("=" * 70)
    print("🔍 Wallex API — Raw JSON Debug")
    print("=" * 70)

    token = getpass("Paste View token (hidden): ").strip()
    if not token:
        print("❌ No token. Exiting.")
        return

    headers = {
        "x-api-key": token,
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=15) as client:
        # 1. Balance
        await debug_endpoint(client, "balance", "GET", "/v1/account/balances", headers=headers)

        # 2. Order Book
        await debug_endpoint(client, "order_book", "GET", "/v1/depth", params={"symbol": "BTCTMN"}, headers=headers)

        # 3. Positions
        await debug_endpoint(client, "positions", "GET", "/margin-trade/v1/positions", params={"active": "true", "position_side": "short"}, headers=headers)

        # 4. Dry Run - Variation A (strings, side=short)
        dry_payload_a = {
            "collateral": "100000", "market": "BTCTMN", "open_price": "21500000000",
            "risk_coef": "1", "side": "short"
        }
        await debug_endpoint(client, "dry_run_A(short_str)", "POST", "/margin-trade/v1/public/dry-run", json=dry_payload_a, headers=headers)

        # 4b. Dry Run - Variation B (side=sell)
        dry_payload_b = {
            "collateral": "100000", "market": "BTCTMN", "open_price": "21500000000",
            "risk_coef": "1", "side": "sell"
        }
        await debug_endpoint(client, "dry_run_B(sell_str)", "POST", "/margin-trade/v1/public/dry-run", json=dry_payload_b, headers=headers)

        # 4c. Dry Run - Variation C (ints, side=short)
        dry_payload_c = {
            "collateral": 100000, "market": "BTCTMN", "open_price": 21500000000,
            "risk_coef": 1, "side": "short"
        }
        await debug_endpoint(client, "dry_run_C(short_int)", "POST", "/margin-trade/v1/public/dry-run", json=dry_payload_c, headers=headers)

    print("\n" + "=" * 70)
    print("✅ Debug complete. Copy ALL output above.")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(main())
