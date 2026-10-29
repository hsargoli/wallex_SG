import pytest
from unittest.mock import AsyncMock, MagicMock
from decimal import Decimal
from app.services.bots.bear_hunter.executor import execute_short_entry
from app.services.bots.bear_hunter.pre_flight import PreFlightResult
from app.services.bots.bear_hunter.state import BearHunterState
from app.services.bots.bear_hunter.config import BearHunterConfig
from app.domain.ports.margin_exchange import MarginPosition

class MockSignal:
    size_tmn = Decimal("15000")
    market = "BTCTMN"
    entry_price = Decimal("1000")
    stop_loss = Decimal("1030")
    take_profit = Decimal("955")
    is_paper = False

def make_pos(pid: str) -> MarginPosition:
    return MarginPosition(
        position_id=pid, market="BTCTMN", side="short", collateral=15000,
        entry_price=1000, current_price=1000, liquidation_price=1200,
        call_price=1100, risk_coef=1, profit_percentage=0, loan_amount=15000,
        interest=0, stop_loss=1030, take_profit=955, state="open", extend_time=3600
    )

@pytest.mark.asyncio
async def test_execute_short_entry_success(tmp_path, monkeypatch):
    monkeypatch.setattr("app.services.bots.bear_hunter.audit.audit_trail.path", tmp_path / "audit.jsonl")
    state = BearHunterState()
    state.initialized = True
    state.paper_mode = False  # <--- CRITICAL FIX: Disable paper mode for live test
    config = BearHunterConfig()
    signal = MockSignal()
    pre_flight = PreFlightResult(approved=True, phase="E")
    
    adapter = MagicMock()
    adapter.open_position = AsyncMock(return_value=make_pos("pos-1"))

    pos = await execute_short_entry(signal, pre_flight, state, config, adapter)
    
    assert pos is not None
    assert pos.position_id == "pos-1"
    assert len(state.open_positions) == 1
    assert state.trades_today == 1
    assert state.daily_volume_tmn == 15000.0
    assert state.last_trade_at is not None

@pytest.mark.asyncio
async def test_execute_short_entry_rejected_by_pre_flight(tmp_path, monkeypatch):
    monkeypatch.setattr("app.services.bots.bear_hunter.audit.audit_trail.path", tmp_path / "audit.jsonl")
    state = BearHunterState()
    state.initialized = True
    state.paper_mode = False
    config = BearHunterConfig()
    signal = MockSignal()
    pre_flight = PreFlightResult(approved=False, reason="test")
    adapter = MagicMock()

    pos = await execute_short_entry(signal, pre_flight, state, config, adapter)
    assert pos is None
    adapter.open_position.assert_not_called()

@pytest.mark.asyncio
async def test_execute_short_entry_exchange_failure(tmp_path, monkeypatch):
    monkeypatch.setattr("app.services.bots.bear_hunter.audit.audit_trail.path", tmp_path / "audit.jsonl")
    state = BearHunterState()
    state.initialized = True
    state.paper_mode = False  # <--- CRITICAL FIX
    config = BearHunterConfig()
    signal = MockSignal()
    pre_flight = PreFlightResult(approved=True, phase="E")
    adapter = MagicMock()
    adapter.open_position = AsyncMock(side_effect=Exception("Exchange Error"))

    pos = await execute_short_entry(signal, pre_flight, state, config, adapter)
    assert pos is None
    assert len(state.open_positions) == 0
    assert state.trades_today == 0
