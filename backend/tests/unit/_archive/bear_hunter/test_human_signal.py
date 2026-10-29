"""Phase 0: HumanSignal tests (datetime-based, migration, check_index, Phase A complete)."""
import json
import pytest
from datetime import datetime, timezone, timedelta
from decimal import Decimal

from app.services.bots.bear_hunter.state import (
    BearHunterState, HumanSignal, StateStore, utcnow,
)
from app.services.bots.bear_hunter.pre_flight import pre_flight_check
from app.services.bots.bear_hunter.config import BearHunterConfig
from app.domain.ports.margin_exchange import (
    MarginExchangePort, DryRunResult, OrderBookInfo,
)


class MockAdapter(MarginExchangePort):
    async def dry_run(self, **kw):
        return DryRunResult(
            liquidity_price=120000, call_price=110000, open_fee=10, trade_fee=10,
            extend_fee=0, loan_amount=15000, max_age=86400, risk_coef=1,
        )
    async def open_position(self, **kw):
        raise NotImplementedError
    async def get_positions(self, active=True):
        return []
    async def close_position(self, pid, price):
        raise NotImplementedError
    async def get_balance(self):
        return 200_000.0
    async def get_order_book(self, market):
        return OrderBookInfo(spread_pct=0.1, best_bid=100000, best_ask=100100)


class MockSignal:
    size_tmn = Decimal("15000")
    market = "BTCTMN"
    entry_price = Decimal("100000")
    stop_loss = Decimal("103000")
    take_profit = Decimal("95500")
    sl_pct = Decimal("3.0")
    tp_pct = Decimal("4.5")
    current_price = Decimal("100000")
    age_seconds = 0
    is_paper = True


@pytest.fixture(autouse=True)
def _isolate_audit(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "app.services.bots.bear_hunter.audit.audit_trail.path",
        tmp_path / "audit.jsonl",
    )


def _full_phase_a_state(direction="bearish"):
    """Complete state with all Phase A checks configured to pass."""
    state = BearHunterState()
    state.initialized = True
    state.paper_mode = True
    state.kill_switch_auto = False
    state.kill_switch_manual = False
    state.last_user_seen_at = utcnow()
    state.set_signal(direction, 10, set_by="test")
    return state


# ═══ Test 1: No signal → reject with check_index ═══
@pytest.mark.asyncio
async def test_no_human_signal_rejected():
    state = _full_phase_a_state()
    state.human_signal = None
    result = await pre_flight_check(MockSignal(), state, BearHunterConfig(), MockAdapter())
    assert result.approved is False
    assert result.reason == "no_human_signal"
    assert result.check_index >= 0


# ═══ Test 2: Expired (datetime) ═══
@pytest.mark.asyncio
async def test_expired_signal_rejected():
    state = _full_phase_a_state()
    past = utcnow() - timedelta(days=1)
    state.human_signal = HumanSignal(
        direction="bearish", set_at=past - timedelta(days=10),
        expires_at=past, set_by="test", note="expired",
    )
    result = await pre_flight_check(MockSignal(), state, BearHunterConfig(), MockAdapter())
    assert result.reason == "human_signal_expired"


# ═══ Test 3: Bullish rejected ═══
@pytest.mark.asyncio
async def test_bullish_signal_rejected():
    state = _full_phase_a_state(direction="bullish")
    result = await pre_flight_check(MockSignal(), state, BearHunterConfig(), MockAdapter())
    assert result.reason == "signal_is_bullish"


# ═══ Test 4: Neutral rejected ═══
@pytest.mark.asyncio
async def test_neutral_signal_rejected():
    state = _full_phase_a_state(direction="neutral")
    result = await pre_flight_check(MockSignal(), state, BearHunterConfig(), MockAdapter())
    assert result.reason == "signal_is_neutral"


# ═══ Test 5: Full Phase A with bearish signal passes ALL checks ═══
@pytest.mark.asyncio
async def test_phase_a_passes_completely_with_bearish():
    state = _full_phase_a_state(direction="bearish")
    result = await pre_flight_check(MockSignal(), state, BearHunterConfig(), MockAdapter())
    # Phase A passes completely
    for check in ["initialized", "kill_switch", "paper_mode",
                  "human_signal_present", "human_signal_not_expired",
                  "signal_bearish", "presence", "signal_freshness"]:
        assert check in result.checks_passed, f"missing: {check}"


# ═══ Test 6: current_regime derived ═══
def test_current_regime_derived():
    state = BearHunterState()
    assert state.current_regime == "idle"
    state.set_signal("bearish", 10)
    assert state.current_regime == "bear"
    state.set_signal("bullish", 10)
    assert state.current_regime == "bull"
    state.set_signal("neutral", 10)
    assert state.current_regime == "range"


# ═══ Test 7: Validation ═══
def test_set_signal_validation():
    state = BearHunterState()
    with pytest.raises(ValueError, match="Invalid direction"):
        state.set_signal("short", 10)
    with pytest.raises(ValueError, match="Invalid ttl_days"):
        state.set_signal("bearish", 0)
    with pytest.raises(ValueError, match="Invalid ttl_days"):
        state.set_signal("bearish", 100)


# ═══ Test 8: note field preserved ═══
def test_note_field():
    state = BearHunterState()
    state.set_signal("bearish", 10, note="ETF news, 20-day cycle")
    assert state.human_signal.note == "ETF news, 20-day cycle"


# ═══ Test 9: set_signal does NOT close open positions ═══
def test_set_signal_preserves_open_positions():
    from app.domain.ports.margin_exchange import MarginPosition
    state = BearHunterState()
    state.set_signal("bearish", 10)
    fake_pos = MarginPosition(
        position_id="pos-1", market="BTCTMN", side="short",
        collateral=1000, entry_price=100, current_price=100,
        liquidation_price=200, call_price=150, risk_coef=1,
        profit_percentage=0, loan_amount=0, interest=0,
        stop_loss=103, take_profit=95, state="open", extend_time=0,
    )
    state.open_positions.append(fake_pos)
    # Change signal
    state.set_signal("bullish", 10)
    # Position MUST still be there
    assert len(state.open_positions) == 1
    assert state.open_positions[0].position_id == "pos-1"


# ═══ Test 10: Migration — legacy bear without human_signal → kill switch ═══
def test_migration_legacy_bear_triggers_kill():
    legacy = {
        "version": 1,
        "state": {
            "initialized": True,
            "paper_mode": False,
            "current_regime": "bear",  # legacy field
            "human_signal": None,
            "capital_tmn": 100000.0,
            "kill_switch_auto": False,
            "kill_switch_manual": False,
        },
    }
    state = BearHunterState.from_dict(legacy["state"])
    assert state.kill_switch_auto is True
    assert "legacy_bear" in state.kill_switch_reason
    assert state.human_signal is None


# ═══ Test 11: Migration — legacy range without human_signal → NO kill ═══
def test_migration_legacy_range_no_kill():
    legacy = {
        "initialized": True,
        "paper_mode": False,
        "current_regime": "range",  # not bear, so safe
        "human_signal": None,
    }
    state = BearHunterState.from_dict(legacy)
    assert state.kill_switch_auto is False
    assert state.human_signal is None


# ═══ Test 12: Roundtrip with datetime HumanSignal ═══
def test_roundtrip_datetime_signal(tmp_path):
    store = StateStore(path=str(tmp_path / "state.json"))
    state = BearHunterState()
    state.paper_mode = False
    state.set_signal("bearish", 10, set_by="test", note="roundtrip test")
    store.bootstrap(state)

    loaded = store.load()
    assert loaded.human_signal is not None
    assert loaded.human_signal.direction == "bearish"
    assert loaded.human_signal.note == "roundtrip test"
    assert isinstance(loaded.human_signal.set_at, datetime)
    assert isinstance(loaded.human_signal.expires_at, datetime)
