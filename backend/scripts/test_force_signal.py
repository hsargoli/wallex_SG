"""Force signal test: bypass RSI, test full pipeline (open, close, PnL)."""
import sys
import asyncio
from pathlib import Path
from decimal import Decimal
from unittest.mock import MagicMock

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app.services.bots.bear_hunter.state import BearHunterState, StateStore
from app.services.bots.bear_hunter.config import BearHunterConfig
from app.services.bots.bear_hunter.runner import Signal
from app.services.bots.bear_hunter.executor import execute_short_entry, close_paper_position
from app.services.bots.bear_hunter.pre_flight import PreFlightResult
from app.services.bots.bear_hunter.paths import USERS_DIR


async def main():
    print("=" * 60)
    print("Force Signal Test (bypass RSI)")
    print("=" * 60)

    # 1. Cleanup
    test_file = USERS_DIR / "test_force.json"
    if test_file.exists():
        test_file.unlink()
        print(f"🧹 Cleaned: {test_file}")

    # 2. Create state (initialized=False by default)
    state = BearHunterState()
    state.capital_tmn = 5_000_000.0
    state.paper_mode = True
    state.set_signal("bearish", 10, set_by="test")
    # Note: do NOT set state.initialized = True — bootstrap does that

    store = StateStore(path=str(test_file))
    store.bootstrap(state)
    print(f"✅ State bootstrapped. initialized={state.initialized}, capital={state.capital_tmn}")

    config = BearHunterConfig()
    adapter = MagicMock()

    # 3. Force signal
    signal = Signal(
        market="BTCTMN",
        size_tmn=Decimal("500000"),  # 10% of 5M
        entry_price=Decimal("21500000000"),
        stop_loss=Decimal("21822500000"),  # +1.5%
        take_profit=Decimal("20855000000"),  # -3%
        sl_pct=Decimal("1.5"),
        tp_pct=Decimal("3.0"),
        current_price=Decimal("21500000000"),
        is_paper=True,
    )

    pre_flight = PreFlightResult(approved=True, phase="TEST")

    # 4. Open
    print("\nOpening virtual position...")
    pos = await execute_short_entry(signal, pre_flight, state, config, adapter)
    if not pos:
        print("❌ Failed to open position")
        return
    print(f"✅ Opened: {pos.position_id}")
    print(f"   Entry: {pos.entry_price}, SL: {pos.stop_loss}, TP: {pos.take_profit}")
    print(f"   Positions count: {len(state.open_positions)}")

    # 5. Simulate TP hit
    print("\nSimulating TP hit (price drops to 20,855,000,000)...")
    exit_price = Decimal("20855000000")
    pnl = await close_paper_position(pos.position_id, exit_price, state, config)
    print(f"✅ Closed at {exit_price}")
    print(f"   PnL: {pnl:,.0f} TMN")
    print(f"   Positions after close: {len(state.open_positions)}")
    print(f"   Capital after: {state.capital_tmn:,.0f} TMN")

    # 6. Cleanup
    test_file.unlink(missing_ok=True)
    print("\n✅ FORCE SIGNAL TEST PASSED")


if __name__ == "__main__":
    asyncio.run(main())
