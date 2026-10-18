"""
Test Wallex Margin API with a View token.
SAFETY: Uses getpass (no token in shell history).
SAFETY: Only calls read-only endpoints + dry_run (simulation).
NEVER calls open_position or close_position.
"""
import asyncio
import sys
from getpass import getpass

sys.path.insert(0, ".")

from app.infrastructure.exchange.wallex.margin_adapter import WallexMarginAdapter


async def main():
    print("=" * 60)
    print("🔍 Wallex Margin API — View Token Test")
    print("=" * 60)

    token = getpass("Paste View token (hidden): ")
    if not token.strip():
        print("❌ No token provided. Exiting.")
        return

    adapter = WallexMarginAdapter(api_key=token.strip())
    print(f"Adapter: {adapter!r}")
    print()

    # ─── TEST 1: get_balance (spot, safest) ───
    print("─" * 60)
    print("TEST 1: get_balance (spot) — control test")
    print("─" * 60)
    try:
        balance = await adapter.get_balance()
        print(f"✅ Balance: {balance:,.2f} TMN")
    except Exception as e:
        print(f"❌ get_balance failed: {type(e).__name__}: {e}")
    print()

    # ─── TEST 2: get_order_book (public-ish) ───
    print("─" * 60)
    print("TEST 2: get_order_book(BTCTMN) — public data")
    print("─" * 60)
    try:
        ob = await adapter.get_order_book("BTCTMN")
        print(f"✅ OrderBook: bid={ob.best_bid:,.0f} ask={ob.best_ask:,.0f} spread={ob.spread_pct:.4f}%")
    except Exception as e:
        print(f"❌ get_order_book failed: {type(e).__name__}: {e}")
    print()

    # ─── TEST 3: get_positions (margin, read-only) ───
    print("─" * 60)
    print("TEST 3: get_positions (margin) — read-only")
    print("─" * 60)
    try:
        positions = await adapter.get_positions(active=True)
        print(f"✅ Positions: {len(positions)} active")
        for p in positions:
            print(f"   • {p.position_id} {p.market} {p.side} entry={p.entry_price:,.0f}")
    except Exception as e:
        print(f"❌ get_positions failed: {type(e).__name__}: {e}")
        print("   ⚠️  If 403: View token has no margin permission.")
    print()

    # ─── TEST 4: dry_run (margin, simulation only) ───
    print("─" * 60)
    print("TEST 4: dry_run (margin) — SIMULATION ONLY (no real position)")
    print("─" * 60)
    print("⚠️  This calls POST but should NOT open a real position.")
    confirm = input("Type exactly 'yes' to proceed, anything else to skip: ").strip()
    if confirm != "yes":
        print("⏭️  Skipped.")
    else:
        try:
            result = await adapter.dry_run(
                collateral="100000",
                market="BTCTMN",
                open_price="21500000000",
                risk_coef="1",
                side="short",
                stop_loss="22200000000",
                take_profit="20500000000",
            )
            print(f"✅ DryRun OK:")
            print(f"   liquidity_price = {result.liquidity_price:,.0f}")
            print(f"   call_price      = {result.call_price:,.0f}")
            print(f"   open_fee        = {result.open_fee}")
            print(f"   trade_fee       = {result.trade_fee}")
            print(f"   loan_amount     = {result.loan_amount:,.0f}")
        except Exception as e:
            print(f"❌ dry_run failed: {type(e).__name__}: {e}")
    print()

    # ─── After dry_run: manual check ───
    print("=" * 60)
    print("⚠️  AFTER dry_run, GO TO WALL.EX PANEL AND VERIFY:")
    print("   1. NO new margin position was opened.")
    print("   2. NO real order was placed.")
    print("   If ANY position appeared → STOP. dry_run is dangerous. Report immediately.")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
