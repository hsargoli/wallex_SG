"""Presence Tracker tests: boundaries + should_* interface + heartbeat + alert rate-limit."""
import asyncio
import pytest
from datetime import timedelta
from unittest.mock import AsyncMock

from app.services.bots.bear_hunter.presence import (
    PresenceTracker, PresenceLevel, PRESENCE_ALERT_COOLDOWN_HOURS,
)
from app.services.bots.bear_hunter.state import BearHunterState, utcnow
from app.services.bots.bear_hunter.config import BearHunterConfig


def _state_at_hours(h: float) -> BearHunterState:
    state = BearHunterState()
    state.initialized = True
    state.paper_mode = False
    state.last_user_seen_at = utcnow() - timedelta(hours=h)
    return state


@pytest.fixture
def tracker():
    return PresenceTracker(config=BearHunterConfig())


# ═══ Boundary tests (>= semantics) ═══
def test_exact_4799h_is_normal(tracker):
    state = _state_at_hours(48)
    state.last_user_seen_at = utcnow() - timedelta(hours=48, seconds=-1)
    assert tracker.current_level(state) == PresenceLevel.NORMAL


def test_exact_48h_is_day2(tracker):
    assert tracker.current_level(_state_at_hours(48)) == PresenceLevel.DAY2


def test_exact_72h_is_day3(tracker):
    assert tracker.current_level(_state_at_hours(72)) == PresenceLevel.DAY3


def test_exact_96h_is_day4(tracker):
    assert tracker.current_level(_state_at_hours(96)) == PresenceLevel.DAY4


# ═══ should_* interface ═══
def test_should_block_false_at_47h(tracker):
    assert tracker.should_block_new_entries(_state_at_hours(47)) is False


def test_should_block_true_at_48h(tracker):
    assert tracker.should_block_new_entries(_state_at_hours(48)) is True


def test_should_block_true_at_all_absent_levels(tracker):
    for h in (48, 72, 96):
        assert tracker.should_block_new_entries(_state_at_hours(h)) is True, f"failed at {h}h"


def test_should_close_profitable_only_at_day3(tracker):
    assert tracker.should_close_profitable(_state_at_hours(47)) is False
    assert tracker.should_close_profitable(_state_at_hours(48)) is False
    assert tracker.should_close_profitable(_state_at_hours(71)) is False
    assert tracker.should_close_profitable(_state_at_hours(72)) is True
    assert tracker.should_close_profitable(_state_at_hours(90)) is True
    assert tracker.should_close_profitable(_state_at_hours(96)) is False


def test_should_close_all_only_at_day4(tracker):
    assert tracker.should_close_all(_state_at_hours(0)) is False
    assert tracker.should_close_all(_state_at_hours(48)) is False
    assert tracker.should_close_all(_state_at_hours(72)) is False
    assert tracker.should_close_all(_state_at_hours(95)) is False
    assert tracker.should_close_all(_state_at_hours(96)) is True
    assert tracker.should_close_all(_state_at_hours(200)) is True


# ═══ Heartbeat ═══
def test_heartbeat_resets_presence_level(tracker):
    state = _state_at_hours(97)
    assert tracker.current_level(state) == PresenceLevel.DAY4
    tracker.heartbeat(state)
    assert tracker.current_level(state) == PresenceLevel.NORMAL
    assert tracker.hours_absent(state) < 1


def test_heartbeat_does_not_reset_kill_switch(tracker):
    state = _state_at_hours(97)
    state.mark_kill_switch("test", source="auto")
    tracker.heartbeat(state)
    assert state.is_killed is True
    assert tracker.current_level(state) == PresenceLevel.NORMAL


# ═══ Alert: rate-limit + timeout ═══
@pytest.mark.asyncio
async def test_alert_fires_first_time():
    cb = AsyncMock()
    tracker = PresenceTracker(config=BearHunterConfig(), alert_callback=cb)
    state = _state_at_hours(49)
    await tracker.check_and_alert(state)
    cb.assert_awaited_once()
    assert state.last_presence_alert_at is not None


@pytest.mark.asyncio
async def test_alert_skipped_during_cooldown():
    cb = AsyncMock()
    tracker = PresenceTracker(config=BearHunterConfig(), alert_callback=cb)
    state = _state_at_hours(49)
    await tracker.check_and_alert(state)
    await tracker.check_and_alert(state)
    assert cb.await_count == 1


@pytest.mark.asyncio
async def test_alert_fires_after_cooldown():
    cb = AsyncMock()
    tracker = PresenceTracker(config=BearHunterConfig(), alert_callback=cb)
    state = _state_at_hours(49)
    await tracker.check_and_alert(state)
    state.last_presence_alert_at = utcnow() - timedelta(hours=PRESENCE_ALERT_COOLDOWN_HOURS + 1)
    await tracker.check_and_alert(state)
    assert cb.await_count == 2


@pytest.mark.asyncio
async def test_alert_does_not_fire_at_normal():
    cb = AsyncMock()
    tracker = PresenceTracker(config=BearHunterConfig(), alert_callback=cb)
    state = _state_at_hours(10)
    await tracker.check_and_alert(state)
    cb.assert_not_called()
    assert state.last_presence_alert_at is None


@pytest.mark.asyncio
async def test_alert_timeout_does_not_crash():
    async def slow_cb(level, hours):
        await asyncio.sleep(10)
    # Use 0.05s timeout (not 5s) — keeps test suite fast
    tracker = PresenceTracker(
        config=BearHunterConfig(),
        alert_callback=slow_cb,
        alert_timeout_seconds=0.05,
    )
    state = _state_at_hours(49)
    level = await tracker.check_and_alert(state)
    assert level == PresenceLevel.DAY2
    assert state.last_presence_alert_at is None


@pytest.mark.asyncio
async def test_alert_callback_exception_does_not_crash():
    async def failing_cb(level, hours):
        raise RuntimeError("telegram down")
    tracker = PresenceTracker(config=BearHunterConfig(), alert_callback=failing_cb)
    state = _state_at_hours(49)
    level = await tracker.check_and_alert(state)
    assert level == PresenceLevel.DAY2
    assert state.last_presence_alert_at is None

def test_heartbeat_does_not_clear_idle(tracker):
    """DAY4 → kill_switch set (manual) → heartbeat resets presence but NOT kill.
    User must explicitly reset via API (future: POST /bear-hunter/resume)."""
    state = _state_at_hours(97)  # DAY4 level
    state.mark_kill_switch("presence_day4_close_all", source="manual")
    assert state.is_killed is True
    assert state.bot_status == "killed_manual"

    tracker.heartbeat(state)
    assert tracker.current_level(state) == PresenceLevel.NORMAL
    # Kill stays -> bot still killed
    assert state.is_killed is True
    assert state.bot_status == "killed_manual"


@pytest.mark.asyncio
async def test_heartbeat_resets_alert_cooldown():
    """After heartbeat, next absence period fires alert immediately."""
    cb = AsyncMock()
    tracker = PresenceTracker(config=BearHunterConfig(), alert_callback=cb)
    state = _state_at_hours(49)

    # First absence: alert fires
    await tracker.check_and_alert(state)
    assert cb.await_count == 1
    assert state.last_presence_alert_at is not None

    # User returns
    tracker.heartbeat(state)
    assert state.last_presence_alert_at is None  # ← key assertion

    # User goes absent again -> alert fires immediately (no cooldown carry-over)
    state.last_user_seen_at = utcnow() - timedelta(hours=49)
    await tracker.check_and_alert(state)
    assert cb.await_count == 2

