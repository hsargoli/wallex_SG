import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from decimal import Decimal
from app.services.bots.bear_hunter.runner import BearHunterRunner
from app.services.bots.bear_hunter.config import BearHunterConfig
from app.services.bots.bear_hunter.state import StateStore, BearHunterState
from app.domain.ports.margin_exchange import MarginExchangePort, MarginPosition, DryRunResult

class MockMarginAdapter(MarginExchangePort):
    async def dry_run(self, **kwargs):
        return DryRunResult(liquidity_price=30000, call_price=25000, open_fee=10, trade_fee=10, extend_fee=0, loan_amount=15000, max_age=86400, risk_coef=1)
    async def open_position(self, **kwargs):
        return MarginPosition(position_id="mock-123", market="BTCTMN", side="short", collateral=15000, entry_price=21000, current_price=21000, liquidation_price=30000, call_price=25000, risk_coef=1, profit_percentage=0, loan_amount=15000, interest=0, stop_loss=21630, take_profit=19845, state="open", extend_time=3600)
    async def get_positions(self, active=True): return []
    async def close_position(self, position_id, price): pass
    async def get_balance(self): return 100_000.0
    async def get_order_book(self, market): return MagicMock(spread_pct=0.1)

@pytest.mark.asyncio
async def test_runner_full_tick(tmp_path, monkeypatch):
    monkeypatch.setattr("app.services.bots.bear_hunter.audit.audit_trail.path", tmp_path / "audit.jsonl")
    
    store = StateStore(path=str(tmp_path / "state.json"))
    state = BearHunterState()
    state.paper_mode = False # We want it to execute
    state.set_signal("bearish", 10)  # Phase 0: require explicit signal
    store.bootstrap(state) # bootstrap sets initialized = True

    config = BearHunterConfig()
    adapter = MockMarginAdapter()
    runner = BearHunterRunner(config, store, adapter, tick_interval_sec=1)
    
    await runner.tick()
    
    assert len(runner.state.open_positions) == 1
    assert runner.state.open_positions[0].position_id == "mock-123"
    assert runner.state.trades_today == 1

@pytest.mark.asyncio
async def test_runner_lock_prevents_overlap(tmp_path, monkeypatch):
    monkeypatch.setattr("app.services.bots.bear_hunter.audit.audit_trail.path", tmp_path / "audit.jsonl")
    store = StateStore(path=str(tmp_path / "state.json"))
    state = BearHunterState()
    state.paper_mode = False
    store.bootstrap(state)

    runner = BearHunterRunner(BearHunterConfig(), store, MockMarginAdapter(), tick_interval_sec=1)
    
    # Manually acquire the lock to simulate a stuck tick
    await runner._lock.acquire()
    
    # Call _safe_tick. It should see the lock and return immediately without executing tick.
    with patch.object(runner, 'tick', new_callable=AsyncMock) as mock_tick:
        await runner._safe_tick()
        mock_tick.assert_not_called()
        
    runner._lock.release()

@pytest.mark.asyncio
async def test_runner_paper_mode_never_calls_open_position(tmp_path, monkeypatch):
    """paper_mode=True must NOT call adapter.open_position. Uses virtual PaperExecutor."""
    monkeypatch.setattr("app.services.bots.bear_hunter.audit.audit_trail.path", tmp_path / "audit.jsonl")
    
    store = StateStore(path=str(tmp_path / "state.json"))
    state = BearHunterState()
    state.paper_mode = True  # <-- CRITICAL: paper mode
    state.set_signal("bearish", 10)  # Phase 0: require explicit signal
    store.bootstrap(state)
    
    adapter = MockMarginAdapter()
    # If open_position is called, test MUST fail
    adapter.open_position = AsyncMock(side_effect=AssertionError("open_position() called in paper_mode!"))
    
    runner = BearHunterRunner(BearHunterConfig(), store, adapter, tick_interval_sec=1)
    await runner.tick()
    
    # Verify virtual position created
    assert len(runner.state.open_positions) == 1
    assert runner.state.open_positions[0].position_id.startswith("paper-")
    assert runner.state.open_positions[0].side == "short"
    # Verify adapter.open_position was NEVER called
    adapter.open_position.assert_not_called()
