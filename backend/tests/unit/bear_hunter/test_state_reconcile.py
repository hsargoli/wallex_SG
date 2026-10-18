import json
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services.bots.bear_hunter.state import (
    BearHunterState, StateStore, reconcile, STATE_VERSION,
)
from app.domain.ports.margin_exchange import MarginPosition


def make_pos(pid: str) -> MarginPosition:
    return MarginPosition(
        position_id=pid, market="BTCTMN", side="short", collateral=100,
        entry_price=100, current_price=100, liquidation_price=120,
        call_price=110, risk_coef=1, profit_percentage=0,
        loan_amount=100, interest=0, stop_loss=103, take_profit=97,
        state="open", extend_time=3600,
    )


def test_save_load_roundtrip(tmp_path):
    store = StateStore(path=str(tmp_path / "state.json"))
    state = BearHunterState()
    state.paper_mode = False
    state.capital_tmn = 250_000.0
    state.trades_today = 2
    state.pnl_8h_pct = -1.5
    store.bootstrap(state)
    state2 = store.load()
    assert state2.initialized is True
    assert state2.capital_tmn == 250_000.0
    assert state2.trades_today == 2
    assert state2.pnl_8h_pct == -1.5
    assert state2.paper_mode is False


def test_corrupt_file_kill_switch(tmp_path):
    path = tmp_path / "state.json"
    path.write_text("{ not valid json !!!", encoding="utf-8")
    store = StateStore(path=str(path))
    state = store.load()
    assert state.kill_switch_auto is True
    assert "state_file_corrupted" in state.kill_switch_reason


def test_save_skipped_when_not_initialized(tmp_path):
    store = StateStore(path=str(tmp_path / "state.json"))
    state = BearHunterState()
    store.save(state)
    assert not (tmp_path / "state.json").exists()


def test_bootstrap_only_once(tmp_path):
    store = StateStore(path=str(tmp_path / "state.json"))
    state = BearHunterState()
    store.bootstrap(state)
    with pytest.raises(ValueError, match="already bootstrapped"):
        store.bootstrap(state)


@pytest.mark.asyncio
async def test_reconcile_unknown_positions():
    state = BearHunterState()
    state.initialized = True
    state.open_positions = []
    adapter = MagicMock()
    adapter.get_positions = AsyncMock(return_value=[make_pos("pos-1")])
    warnings = await reconcile(state, adapter)
    assert state.kill_switch_auto is True
    assert "unknown_positions_detected" in state.kill_switch_reason
    assert len(warnings) == 1


@pytest.mark.asyncio
async def test_reconcile_closed_positions():
    state = BearHunterState()
    state.initialized = True
    state.open_positions = [make_pos("pos-1")]
    adapter = MagicMock()
    adapter.get_positions = AsyncMock(return_value=[])
    warnings = await reconcile(state, adapter)
    assert state.kill_switch_auto is False
    assert len(warnings) == 1
    assert "closed on exchange" in warnings[0]
    assert state.open_positions == []


def test_paper_started_at_auto_init():
    state = BearHunterState(paper_mode=True)
    assert state.paper_started_at is not None


def test_backup_rotation(tmp_path):
    store = StateStore(path=str(tmp_path / "state.json"), max_backups=3)
    state = BearHunterState()
    store.bootstrap(state)
    for i in range(10):
        state.trades_today = i
        store.save(state)
    backups = list(store.backup_dir.glob("state-*.json"))
    assert len(backups) <= 3
