"""Phase 1C: BotLifecycleManager — regime-based bot switching."""
from app.services.bots.sarv_router.config import SarvRouterConfig
from app.services.bots.sarv_router.regime import Regime
from app.services.bots.sarv_router.bot_lifecycle import BotLifecycleManager


def _mk(config=None):
    cfg = config or SarvRouterConfig()
    calls = {"start": [], "stop": [], "stop_all": 0}
    def _start(slug): calls["start"].append(slug)
    def _stop(slug): calls["stop"].append(slug)
    def _stop_all(): calls["stop_all"] += 1
    mgr = BotLifecycleManager(cfg, _start, _stop, _stop_all)
    return mgr, calls, cfg


class TestBotLifecycle:
    def test_first_call_pending(self):
        mgr, _, _ = _mk()
        r = mgr.update(Regime.UPTREND, now_idx=0)
        assert r["action"] == "pending"

    def test_no_switch_before_stability_window(self):
        mgr, calls, cfg = _mk()
        n = cfg.stability_window
        for i in range(n - 1):
            mgr.update(Regime.UPTREND, now_idx=i)
        assert calls["start"] == []

    def test_switch_after_stability_window(self):
        mgr, calls, cfg = _mk()
        n = cfg.stability_window
        for i in range(n):
            mgr.update(Regime.UPTREND, now_idx=i)
        r = mgr.update(Regime.UPTREND, now_idx=n)
        assert r["action"] == "switched"
        assert calls["start"] == ["nooaah"]

    def test_range_switches_to_sarvban(self):
        mgr, calls, cfg = _mk()
        n = cfg.stability_window
        for i in range(n):
            mgr.update(Regime.RANGE, now_idx=i)
        r = mgr.update(Regime.RANGE, now_idx=n)
        assert r["action"] == "switched"
        assert calls["start"] == ["sarvban"]

    def test_unknown_all_cash(self):
        mgr, calls, cfg = _mk()
        n = cfg.stability_window
        for i in range(n + 5):
            mgr.update(Regime.UNKNOWN, now_idx=i)
        assert mgr.active_bots == []
        assert calls["start"] == []

    def test_downtrend_stops_all(self):
        mgr, calls, cfg = _mk()
        n = cfg.stability_window
        for i in range(n):
            mgr.update(Regime.UPTREND, now_idx=i)
        mgr.update(Regime.UPTREND, now_idx=n)
        assert "nooaah" in calls["start"]
        # Move to downtrend; need stability + cooldown
        base = n
        for i in range(base, base + n + cfg.cooldown_candles + 5):
            mgr.update(Regime.DOWNTREND, now_idx=i)
        assert mgr.active_bots == []
        assert calls["stop_all"] >= 1

    def test_cooldown_blocks_rapid_switch(self):
        cfg = SarvRouterConfig(stability_window=6, cooldown_candles=12)
        mgr, calls, _ = _mk(cfg)
        for i in range(7):
            mgr.update(Regime.UPTREND, now_idx=i)
        assert "nooaah" in calls["start"]
        for i in range(7, 13):
            mgr.update(Regime.RANGE, now_idx=i)
        r = mgr.update(Regime.RANGE, now_idx=13)
        assert r["action"] == "cooldown"

    def test_stability_resets_on_regime_change(self):
        mgr, calls, cfg = _mk()
        n = cfg.stability_window
        for i in range(n - 5):
            mgr.update(Regime.UPTREND, now_idx=i)
        mgr.update(Regime.RANGE, now_idx=n - 5)
        mgr.update(Regime.UPTREND, now_idx=n - 4)
        # Not enough stable yet (since = n-4, so need idx < (n-4) + n)
        for i in range(n - 3, (n - 4) + n):
            r = mgr.update(Regime.UPTREND, now_idx=i)
            assert r["action"] == "pending"
        # At threshold, switch happens
        r = mgr.update(Regime.UPTREND, now_idx=(n - 4) + n)
        assert r["action"] == "switched"

    def test_no_switch_if_already_active(self):
        mgr, calls, cfg = _mk()
        n = cfg.stability_window
        for i in range(n):
            mgr.update(Regime.UPTREND, now_idx=i)
        mgr.update(Regime.UPTREND, now_idx=n)
        assert mgr.active_bots == ["nooaah"]
        r = mgr.update(Regime.UPTREND, now_idx=n + 5)
        assert r["action"] == "no_change"

    def test_fail_safe_on_start_error(self):
        def _start(slug): raise RuntimeError("boom")
        def _stop(slug): pass
        def _stop_all(): pass
        cfg = SarvRouterConfig()
        mgr = BotLifecycleManager(cfg, _start, _stop, _stop_all)
        n = cfg.stability_window
        for i in range(n):
            mgr.update(Regime.UPTREND, now_idx=i)
        r = mgr.update(Regime.UPTREND, now_idx=n)
        assert r["action"] == "error"
        assert mgr.active_bots == []
