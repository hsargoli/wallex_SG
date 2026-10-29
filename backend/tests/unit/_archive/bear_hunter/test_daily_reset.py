"""Test: daily_reset preserves realized PnL across day boundary (Di Darya scenario)."""
import pytest
from datetime import datetime, timezone, timedelta
from app.services.bots.bear_hunter.state import BearHunterState


def test_daily_reset_preserves_realized_pnl():
    """
    Scenario from Di Darya:
    - Trade opens day 1 at 23:50 (trades_today=1, daily_volume=500k)
    - UTC midnight passes (day 2)
    - Trade closes day 2 at 00:15 with -0.5% PnL
    - Bug: reset at 00:20 would wipe PnL
    - Fix: add_realized_pnl resets AND then adds, so PnL=-0.5 survives
    """
    state = BearHunterState()
    state.capital_tmn = 5_000_000.0

    # Simulate day 1 state
    day1 = datetime.now(timezone.utc) - timedelta(days=1)
    state.daily_date = day1
    state.trades_today = 1
    state.daily_volume_tmn = 500_000.0
    state.daily_pnl_pct = 0.0

    # Trade closes on day 2 (utcnow) with -0.5%
    state.add_realized_pnl(-0.5)

    # Should reset day1 stats but preserve new PnL
    assert state.trades_today == 0, "trades_today should reset on day change"
    assert state.daily_volume_tmn == 0.0, "volume should reset"
    assert state.daily_pnl_pct == -0.5, "realized PnL MUST survive reset"
    assert state.daily_date.date() == datetime.now(timezone.utc).date()


def test_record_trade_open_resets_new_day():
    """Opening trade on new day resets stats first."""
    state = BearHunterState()
    state.daily_date = datetime.now(timezone.utc) - timedelta(days=1)
    state.trades_today = 3
    state.daily_volume_tmn = 1_500_000.0

    state.record_trade_open(500_000.0)

    assert state.trades_today == 1, "reset then +1"
    assert state.daily_volume_tmn == 500_000.0
    assert state.daily_date.date() == datetime.now(timezone.utc).date()


def test_ensure_daily_reset_same_day_noop():
    """Same day -> no reset."""
    state = BearHunterState()
    state.daily_date = datetime.now(timezone.utc)
    state.trades_today = 2
    state.daily_volume_tmn = 1_000_000.0
    state.daily_pnl_pct = -0.3

    state._ensure_daily_reset()

    assert state.trades_today == 2
    assert state.daily_volume_tmn == 1_000_000.0
    assert state.daily_pnl_pct == -0.3
