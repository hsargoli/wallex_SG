"""Phase 1C: BotLifecycleManager — regime-based bot switching."""
import pytest
from app.services.bots.sarv_router.config import SarvRouterConfig
from app.services.bots.sarv_router.regime import Regime
from app.services.bots.sarv_router.bot_lifecycle import BotLifecycleManager


def _mk(config=None):
    calls = {"start": [], "stop": [], "stop_all": 0}
    def _start(slug): calls["start"].append(slug)
    def _stop(slug): calls["stop"].append(slug)
    def _stop_all(): calls["stop_all"] += 1
    mgr = BotLifecycleManager(config or SarvRouterConfig(), _start, _stop, _stop_all)
    return mgr, calls


class TestBotLifecycle:
    def test_first_call_pending(self):
        mgr, calls = _mk()
        r = mgr.update(Regime.UPTREND, now_idx=0)
        assert r["action"] == "pending"
        assert r["reason"] == "regime_changed"

    def test_no_switch_before_stability_window(self):
        mgr, calls = _mk()
        for i in range(23):
            mgr.update(Regime.UPTREND, now_idx=i)
        assert calls["start"] == []

    def test_switch_after_stability_window(self):
        mgr, calls = _mk()
        for i in range(24):
            mgr.update(Regime.UPTREND, now_idx=i)
        r = mgr.update(Regime.UPTREND, now_idx=24)
        assert r["action"] == "switched"
        assert calls["start"] == ["nooaah"]
        assert mgr.active_bots == ["nooaah"]

    def test_range_switches_to_sarvban(self):
        mgr, calls = _mk()
        for i in range(24):
            mgr.update(Regime.RANGE, now_idx=i)
        r = mgr.update(Regime.RANGE, now_idx=24)
        assert r["action"] == "switched"
        assert calls["start"] == ["sarvban"]

    def test_unknown_all_cash(self):
        mgr, calls = _mk()
        for i in range(30):
            mgr.update(Regime.UNKNOWN, now_idx=i)
        assert mgr.active_bots == []
        assert "nooaah" not in calls["start"]
        assert "sarvban" not in calls["start"]

    def test_downtrend_stops_all(self):
        mgr, calls = _mk()
        for i in range(24):
            mgr.update(Regime.UPTREND, now_idx=i)
        mgr.update(Regime.UPTREND, now_idx=24)
        assert "nooaah" in calls["start"]
        for i in range(25, 50):
            mgr.update(Regime.DOWNTREND, now_idx=i)
        assert mgr.active_bots == []
        assert calls["stop_all"] >= 1

    def test_cooldown_blocks_rapid_switch(self):
        cfg = SarvRouterConfig(stability_window=6, cooldown_candles=12)
        mgr, calls = _mk(cfg)
        for i in range(7):
            mgr.update(Regime.UPTREND, now_idx=i)
        assert "nooaah" in calls["start"]
        for i in range(7, 13):
            mgr.update(Regime.RANGE, now_idx=i)
        r = mgr.update(Regime.RANGE, now_idx=13)
        assert r["action"] == "cooldown"

    def test_stability_resets_on_regime_change(self):
        mgr, calls = _mk()
        for i in range(20):
            mgr.update(Regime.UPTREND, now_idx=i)
        mgr.update(Regime.RANGE, now_idx=20)
        mgr.update(Regime.UPTREND, now_idx=21)
        for i in range(22, 45):
            r = mgr.update(Regime.UPTREND, now_idx=i)
            assert r["action"] == "pending"
        r = mgr.update(Regime.UPTREND, now_idx=45)
        assert r["action"] == "switched"

    def test_no_switch_if_already_active(self):
        mgr, calls = _mk()
        for i in range(24):
            mgr.update(Regime.UPTREND, now_idx=i)
        mgr.update(Regime.UPTREND, now_idx=24)
        r = mgr.update(Regime.UPTREND, now_idx=30)
        assert r["action"] == "no_change"

    def test_fail_safe_on_start_error(self):
        def _start(slug): raise RuntimeError("boom")
        def _stop(slug): pass
        def _stop_all(): pass
        mgr = BotLifecycleManager(SarvRouterConfig(), _start, _stop, _stop_all)
        for i in range(24):
            mgr.update(Regime.UPTREND, now_idx=i)
        r = mgr.update(Regime.UPTREND, now_idx=24)
        assert r["action"] == "error"
        assert mgr.active_bots == []
