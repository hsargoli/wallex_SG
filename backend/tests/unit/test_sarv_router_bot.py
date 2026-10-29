"""Phase 1F: SarvRouter — full integration (detect + lifecycle + allocate + store + audit)."""
import uuid
from decimal import Decimal
import pytest
from app.domain.entities.candle import Candle
from app.services.bots.sarv_router.audit import AuditTrail
from app.services.bots.sarv_router.bot import SarvRouter
from app.services.bots.sarv_router.config import SarvRouterConfig
from app.services.bots.sarv_router.regime import Regime
from app.services.bots.sarv_router.store import SarvStore


def _c(t, price):
    p = Decimal(str(price))
    return Candle(time=t, open=p, high=p+1, low=p-1, close=p, volume=Decimal("100"))


def _uptrend(n=200):
    return [_c(i*3600, 100 + i*2) for i in range(n)]


def _downtrend(n=200):
    return [_c(i*3600, 400 - i*2) for i in range(n)]


def _range(n=200):
    return [_c(i*3600, 100 + (i % 2)) for i in range(n)]


def _mk(tmp_path, config=None):
    calls = {"start": [], "stop": [], "stop_all": 0}
    def _start(slug): calls["start"].append(slug)
    def _stop(slug): calls["stop"].append(slug)
    def _stop_all(): calls["stop_all"] += 1
    store = SarvStore(base_dir=tmp_path)
    audit = AuditTrail(base_dir=tmp_path)
    router = SarvRouter(
        config=config or SarvRouterConfig(),
        start_bot=_start, stop_bot=_stop, stop_all=_stop_all,
        store=store, audit=audit,
    )
    return router, calls, store, audit


class TestSarvRouter:
    def test_uptrend_switches_to_nooaah(self, tmp_path):
        router, calls, store, _ = _mk(tmp_path)
        uid = str(uuid.uuid4())
        candles = _uptrend(200)
        router.tick(uid, candles, now_idx=0)   # pending (regime_changed)
        r = router.tick(uid, candles, now_idx=24)  # switched
        assert r["action"] == "switched"
        assert "nooaah" in calls["start"]
        st = store.load(uid)
        assert st.active_bots == ["nooaah"]
        assert st.cash == 400_000.0
        assert st.current_regime == "uptrend"

    def test_downtrend_no_bots_started(self, tmp_path):
        router, calls, store, _ = _mk(tmp_path)
        uid = str(uuid.uuid4())
        candles = _downtrend(200)
        router.tick(uid, candles, now_idx=0)
        router.tick(uid, candles, now_idx=24)
        st = store.load(uid)
        assert st.active_bots == []
        assert st.cash == 1_000_000.0
        assert calls["start"] == []

    def test_kill_switch_manual_blocks(self, tmp_path):
        router, calls, store, _ = _mk(tmp_path)
        uid = str(uuid.uuid4())
        # pre-set manual kill switch
        st = store.load(uid)
        st.kill_switch_manual = True
        store.save(uid, st)
        router.tick(uid, _uptrend(200), now_idx=0)
        assert calls["start"] == []
        assert calls["stop_all"] >= 1

    def test_daily_loss_limit_triggers_auto_kill(self, tmp_path):
        router, calls, store, _ = _mk(tmp_path)
        uid = str(uuid.uuid4())
        st = store.load(uid)
        st.daily_pnl_pct = -3.0  # < -2% limit
        store.save(uid, st)
        r = router.tick(uid, _uptrend(200), now_idx=0)
        assert r["action"] == "daily_loss_kill"
        st2 = store.load(uid)
        assert st2.kill_switch_auto is True
        assert calls["stop_all"] >= 1

    def test_insufficient_data_unknown(self, tmp_path):
        router, calls, store, _ = _mk(tmp_path)
        uid = str(uuid.uuid4())
        few = _uptrend(20)  # < warmup
        router.tick(uid, few, now_idx=0)
        router.tick(uid, few, now_idx=24)
        st = store.load(uid)
        assert st.active_bots == []
        assert calls["start"] == []

    def test_audit_logged_on_switch(self, tmp_path):
        router, calls, store, audit = _mk(tmp_path)
        uid = str(uuid.uuid4())
        candles = _uptrend(200)
        router.tick(uid, candles, now_idx=0)
        router.tick(uid, candles, now_idx=24)
        p = tmp_path / f"{uid}.audit.jsonl"
        assert p.exists()
        lines = [l for l in p.read_text().strip().split("\n") if l]
        # must have at least one "switch" entry
        import json
        types = [json.loads(l)["type"] for l in lines]
        assert "switch" in types

    def test_no_switch_if_already_active(self, tmp_path):
        router, calls, store, _ = _mk(tmp_path)
        uid = str(uuid.uuid4())
        candles = _uptrend(200)
        router.tick(uid, candles, now_idx=0)
        router.tick(uid, candles, now_idx=24)  # switched
        r = router.tick(uid, candles, now_idx=50)  # no_change
        assert r["action"] == "no_change"

    def test_fail_safe_on_start_error(self, tmp_path):
        def _start(slug): raise RuntimeError("boom")
        def _stop(slug): pass
        def _stop_all(): pass
        store = SarvStore(base_dir=tmp_path)
        audit = AuditTrail(base_dir=tmp_path)
        router = SarvRouter(
            config=SarvRouterConfig(), start_bot=_start, stop_bot=_stop,
            stop_all=_stop_all, store=store, audit=audit,
        )
        uid = str(uuid.uuid4())
        candles = _uptrend(200)
        router.tick(uid, candles, now_idx=0)
        r = router.tick(uid, candles, now_idx=24)
        assert r["action"] == "error"
        st = store.load(uid)
        assert st.active_bots == []
