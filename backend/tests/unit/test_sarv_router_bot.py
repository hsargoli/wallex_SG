"""Phase 1F: SarvRouter — full integration."""
import uuid
from decimal import Decimal
from app.domain.entities.candle import Candle
from app.services.bots.sarv_router.audit import AuditTrail
from app.services.bots.sarv_router.bot import SarvRouter
from app.services.bots.sarv_router.config import SarvRouterConfig
from app.services.bots.sarv_router.store import SarvStore


def _c(t, price):
    p = Decimal(str(price))
    return Candle(time=t, open=p, high=p+1, low=p-1, close=p, volume=Decimal("100"))


def _uptrend(n=300):
    return [_c(i*3600, 100 + i*2) for i in range(n)]


def _downtrend(n=300):
    return [_c(i*3600, 700 - i*2) for i in range(n)]


def _mk(tmp_path):
    calls = {"start": [], "stop": [], "stop_all": 0}
    def _start(slug): calls["start"].append(slug)
    def _stop(slug): calls["stop"].append(slug)
    def _stop_all(): calls["stop_all"] += 1
    cfg = SarvRouterConfig()
    router = SarvRouter(
        config=cfg, start_bot=_start, stop_bot=_stop, stop_all=_stop_all,
        store=SarvStore(base_dir=tmp_path), audit=AuditTrail(base_dir=tmp_path),
    )
    return router, calls, cfg


class TestSarvRouter:
    def test_uptrend_switches_to_nooaah(self, tmp_path):
        router, calls, cfg = _mk(tmp_path)
        uid = str(uuid.uuid4())
        candles = _uptrend(300)
        router.tick(uid, candles, now_idx=0)
        r = router.tick(uid, candles, now_idx=cfg.stability_window)
        assert r["action"] == "switched"
        assert "nooaah" in calls["start"]
        st = router.store.load(uid)
        assert st.active_bots == ["nooaah"]
        assert st.current_regime == "uptrend"

    def test_downtrend_no_bots_started(self, tmp_path):
        router, calls, cfg = _mk(tmp_path)
        uid = str(uuid.uuid4())
        candles = _downtrend(300)
        router.tick(uid, candles, now_idx=0)
        router.tick(uid, candles, now_idx=cfg.stability_window)
        st = router.store.load(uid)
        assert st.active_bots == []
        assert calls["start"] == []

    def test_kill_switch_manual_blocks(self, tmp_path):
        router, calls, cfg = _mk(tmp_path)
        uid = str(uuid.uuid4())
        st = router.store.load(uid)
        st.kill_switch_manual = True
        router.store.save(uid, st)
        router.tick(uid, _uptrend(300), now_idx=0)
        assert calls["start"] == []

    def test_daily_loss_limit_triggers_auto_kill(self, tmp_path):
        router, calls, cfg = _mk(tmp_path)
        uid = str(uuid.uuid4())
        st = router.store.load(uid)
        st.daily_pnl_pct = -3.0
        router.store.save(uid, st)
        r = router.tick(uid, _uptrend(300), now_idx=0)
        assert r["action"] == "daily_loss_kill"
        st2 = router.store.load(uid)
        assert st2.kill_switch_auto is True

    def test_insufficient_data_unknown(self, tmp_path):
        router, calls, cfg = _mk(tmp_path)
        uid = str(uuid.uuid4())
        few = _uptrend(20)
        router.tick(uid, few, now_idx=0)
        router.tick(uid, few, now_idx=cfg.stability_window)
        st = router.store.load(uid)
        assert st.active_bots == []
        assert calls["start"] == []

    def test_audit_logged_on_switch(self, tmp_path):
        router, calls, cfg = _mk(tmp_path)
        uid = str(uuid.uuid4())
        router.tick(uid, _uptrend(300), now_idx=0)
        router.tick(uid, _uptrend(300), now_idx=cfg.stability_window)
        p = tmp_path / f"{uid}.audit.jsonl"
        assert p.exists()

    def test_no_switch_if_already_active(self, tmp_path):
        router, calls, cfg = _mk(tmp_path)
        uid = str(uuid.uuid4())
        router.tick(uid, _uptrend(300), now_idx=0)
        router.tick(uid, _uptrend(300), now_idx=cfg.stability_window)
        r = router.tick(uid, _uptrend(300), now_idx=cfg.stability_window + 10)
        assert r["action"] == "no_change"

    def test_fail_safe_on_start_error(self, tmp_path):
        def _start(slug): raise RuntimeError("boom")
        def _stop(slug): pass
        def _stop_all(): pass
        cfg = SarvRouterConfig()
        router = SarvRouter(
            config=cfg, start_bot=_start, stop_bot=_stop, stop_all=_stop_all,
            store=SarvStore(base_dir=tmp_path), audit=AuditTrail(base_dir=tmp_path),
        )
        uid = str(uuid.uuid4())
        router.tick(uid, _uptrend(300), now_idx=0)
        r = router.tick(uid, _uptrend(300), now_idx=cfg.stability_window)
        assert r["action"] == "error"
        assert router.store.load(uid).active_bots == []


def test_tick_persists_regime_since_idx(tmp_path):
    """Regression: regime_since_idx must be persisted to state file after tick.

    Before fix: bot.py::tick() never syncs lifecycle._regime_since_idx
    to state.regime_since_idx. Result: file always has regime_since_idx=null.

    Bug is invisible to existing tests (test_uptrend_switch) because they
    only check state.active_bots — and lifecycle keeps _regime_since_idx
    in memory, not on disk.
    """
    cfg = SarvRouterConfig()
    calls = {"start": [], "stop": [], "stop_all": 0}

    def _start(slug: str) -> None:
        calls["start"].append(slug)

    def _stop(slug: str) -> None:
        calls["stop"].append(slug)

    def _stop_all() -> None:
        calls["stop_all"] += 1

    router = SarvRouter(
        config=cfg,
        start_bot=_start,
        stop_bot=_stop,
        stop_all=_stop_all,
        store=SarvStore(base_dir=tmp_path),
        audit=AuditTrail(base_dir=tmp_path),
    )
    uid = str(uuid.uuid4())
    candles = _uptrend(300)

    r1 = router.tick(uid, candles, now_idx=5)
    assert r1["action"] == "pending"
    assert r1.get("reason") == "regime_changed"

    persisted = router.store.load(uid)
    assert persisted.regime_since_idx == 5, (
        f"regime_since_idx not persisted after regime change: "
        f"got {persisted.regime_since_idx!r}, expected 5"
    )

    half = cfg.stability_window // 2
    r2 = router.tick(uid, candles, now_idx=5 + half)
    assert r2["action"] == "pending"

    persisted2 = router.store.load(uid)
    assert persisted2.regime_since_idx == 5, (
        f"regime_since_idx changed unexpectedly: "
        f"got {persisted2.regime_since_idx!r}, expected 5"
    )
