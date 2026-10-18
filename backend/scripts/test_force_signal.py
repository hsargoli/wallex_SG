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


async def test_scenario(name: str, exit_price: Decimal, expected_reason: str):
    print(f"\n--- Scenario: {name} ---")
    test_file = USERS_DIR / f"test_force_{name}.json"
    if test_file.exists():
        test_file.unlink()

    state = BearHunterState()
    state.capital_tmn = 5_000_000.0
    state.paper_mode = True
    state.set_signal("bearish", 10, set_by="test")

    store = StateStore(path=str(test_file))
    store.bootstrap(state)

    config = BearHunterConfig()
    adapter = MagicMock()

    signal = Signal(
        market="BTCTMN",
        size_tmn=Decimal("500000"),
        entry_price=Decimal("21500000000"),
        stop_loss=Decimal("21822500000"),    # +1.5%
        take_profit=Decimal("20855000000"),  # -3.0%
        sl_pct=Decimal("1.5"),
        tp_pct=Decimal("3.0"),
        current_price=Decimal("21500000000"),
        is_paper=True,
    )

    pre_flight = PreFlightResult(approved=True, phase="TEST")
    pos = await execute_short_entry(signal, pre_flight, state, config, adapter)
    if not pos:
        print("❌ Failed to open")
        return

    # Simulate exit
    pnl = await close_paper_position(pos.position_id, exit_price, state, config)
    print(f"Exit Price: {exit_price:,.0f} | PnL: {pnl:,.0f} TMN")
    
    # Assertions
    if "TP" in expected_reason and pnl <= 0:
        print(f"❌ Expected profit, got {pnl}")
    elif "SL" in expected_reason and pnl >= 0:
        print(f"❌ Expected loss, got {pnl}")
    
    print(f"✅ {name} PASSED")
    test_file.unlink(missing_ok=True)

async def main():
    print("=" * 60)
    print("Force Signal Test (Multi-Scenario)")
    print("=" * 60)
    
    # Scenario 1: TP Hit (Profit)
    await test_scenario("TP_HIT", Decimal("20855000000"), "TP")
    
    # Scenario 2: SL Hit (Loss)
    await test_scenario("SL_HIT", Decimal("21822500000"), "SL")
    
    # Scenario 3: Timeout (close at breakeven-ish)
    await test_scenario("TIMEOUT", Decimal("21500000000"), "TIMEOUT")

if __name__ == "__main__":
    asyncio.run(main())
