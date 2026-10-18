"""Phase 1.2: WAITING_LIQUIDITY + idle + bot_status tests."""
import pytest
from datetime import timedelta
from unittest.mock import AsyncMock
from decimal import Decimal

from app.services.bots.bear_hunter.state import BearHunterState, utcnow, HumanSignal
from app.services.bots.bear_hunter.config import BearHunterConfig
from app.services.bots.bear_hunter.pre_flight import pre_flight_check
from app.domain.ports.margin_exchange import (
    MarginExchangePort, DryRunResult, OrderBookInfo, DryRunError, DryRunReason,
)


class MockAdapter(MarginExchangePort):
    def __init__(self, liquidity_ok: bool = True):
        self.liquidity_ok = liquidity_ok
    async def dry_run(self, **kw):
        if not self.liquidity_ok:
            raise DryRunError(DryRunReason.NO_LIQUIDITY, "ظرفیت تمام شده")
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


def _ready_state(signal_direction="bearish"):
    state = BearHunterState()
    state.initialized = True
    state.paper_mode = True
    state.last_user_seen_at = utcnow()
    state.set_signal(signal_direction, 10, set_by="test")
    return state


# ═══════════════════════════════════════════════════════════════
# bot_status ordering (8 states)
# ═══════════════════════════════════════════════════════════════

def test_bot_status_killed_auto():
    state = _ready_state()
    state.kill_switch_auto = True
    assert state.bot_status == "killed_auto"


def test_bot_status_killed_manual():
    state = _ready_state()
    state.kill_switch_manual = True
    assert state.bot_status == "killed_manual"


def test_bot_status_idle():
    state = _ready_state()
    state.go_idle("test")
    assert state.bot_status == "idle"


def test_bot_status_no_signal():
    state = BearHunterState()
    assert state.bot_status == "no_signal"


def test_bot_status_signal_expired():
    state = _ready_state()
    past = utcnow() - timedelta(days=1)
    state.human_signal = HumanSignal(
        direction="bearish", set_at=past - timedelta(days=10),
        expires_at=past, set_by="test",
    )
    assert state.bot_status == "signal_expired"


def test_bot_status_signal_not_bearish():
    state = _ready_state(signal_direction="bullish")
    assert state.bot_status == "signal_not_bearish"


def test_bot_status_waiting_liquidity():
    state = _ready_state()
    state.mark_waiting_liquidity()
    assert state.bot_status == "waiting_liquidity"


def test_bot_status_active():
    state = _ready_state()
    assert state.bot_status == "active"


# ═══════════════════════════════════════════════════════════════
# mark/clear waiting_liquidity
# ═══════════════════════════════════════════════════════════════

def test_is_waiting_liquidity_false_initially():
    state = BearHunterState()
    assert state.is_waiting_liquidity is False
    assert state.waiting_liquidity_since is None


def test_mark_waiting_liquidity_idempotent():
    state = _ready_state()
    state.mark_waiting_liquidity()
    first_ts = state.waiting_liquidity_since
    state.mark_waiting_liquidity()  # second call
    assert state.waiting_liquidity_since == first_ts  # unchanged


def test_clear_waiting_liquidity():
    state = _ready_state()
    state.mark_waiting_liquidity()
    assert state.is_waiting_liquidity is True
    state.clear_waiting_liquidity()
    assert state.is_waiting_liquidity is False


def test_set_signal_clears_waiting_liquidity():
    state = _ready_state()
    state.mark_waiting_liquidity()
    state.set_signal("bearish", 10)  # same direction, new attempt
    assert state.is_waiting_liquidity is False


# ═══════════════════════════════════════════════════════════════
# idle go/resume
# ═══════════════════════════════════════════════════════════════

def test_go_idle_and_resume():
    state = _ready_state()
    assert state.idle is False
    state.go_idle("test")
    assert state.idle is True
    state.resume_from_idle()
    assert state.idle is False


def test_resume_from_idle_does_not_clear_kill_switch():
    state = _ready_state()
    state.mark_kill_switch("test", source="manual")
    state.go_idle("test")
    state.resume_from_idle()
    assert state.idle is False
    assert state.is_killed is True


# ═══════════════════════════════════════════════════════════════
# pre_flight integration
# ═══════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_pre_flight_rejects_on_idle():
    state = _ready_state()
    state.go_idle("manual")
    result = await pre_flight_check(MockSignal(), state, BearHunterConfig(), MockAdapter())
    assert result.reason == "idle"
    assert result.phase == "A"


@pytest.mark.asyncio
async def test_pre_flight_marks_waiting_on_no_liquidity():
    state = _ready_state()
    assert state.is_waiting_liquidity is False
    result = await pre_flight_check(MockSignal(), state, BearHunterConfig(), MockAdapter(liquidity_ok=False))
    assert result.reason == "no_margin_liquidity"
    assert state.is_waiting_liquidity is True


@pytest.mark.asyncio
async def test_pre_flight_clears_waiting_on_success():
    state = _ready_state()
    state.mark_waiting_liquidity()
    assert state.is_waiting_liquidity is True
    result = await pre_flight_check(MockSignal(), state, BearHunterConfig(), MockAdapter(liquidity_ok=True))
    # dry_run succeeded so waiting cleared, even if later phases reject
    assert state.is_waiting_liquidity is False


# ═══════════════════════════════════════════════════════════════
# Migration
# ═══════════════════════════════════════════════════════════════

def test_migration_waiting_liquidity_since_string():
    data = {
        "initialized": True,
        "paper_mode": False,
        "waiting_liquidity_since": "2026-10-18T05:00:00+00:00",
    }
    state = BearHunterState.from_dict(data)
    assert state.waiting_liquidity_since is not None
    assert isinstance(state.waiting_liquidity_since, type(utcnow()))
