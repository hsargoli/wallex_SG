"""Phase 1 Copilot: DecisionReason — backward compat + Copilot keys.

Per ADR-0040 §2.1 + Addendum 1.1 (Option Y).
"""
import uuid

from app.services.bots.sarv_router.decision import DecisionReason


class TestDecisionReasonContract:
    def test_to_dict_preserves_old_keys(self):
        """ADR-0040 §2.2: consumers relying on old keys must not break."""
        dr = DecisionReason(
            action="switched",
            why="regime=uptrend، پایدار",
            evidence={
                "action": "switched",
                "regime": "uptrend",
                "active_bots": ["nooaah"],
                "tick_id": "test-tick-1",
                "path": "lifecycle",
            },
            confidence=0.9,
            tick_id="test-tick-1",
        )
        d = dr.to_dict()
        assert d["action"] == "switched"
        assert d["regime"] == "uptrend"
        assert d["active_bots"] == ["nooaah"]

    def test_to_dict_has_copilot_keys(self):
        """ADR-0040 §2.1: Copilot keys must be present in all paths."""
        dr = DecisionReason(
            action="pending",
            why="stability_window",
            evidence={"regime": "uptrend", "path": "lifecycle"},
            confidence=0.5,
            tick_id=str(uuid.uuid4()),
        )
        d = dr.to_dict()
        assert "why" in d
        assert "evidence" in d
        assert "confidence" in d
        assert "tick_id" in d
        assert d["evidence"] == dr.evidence


class TestDecisionReasonUniformShape:
    """ADR-0040 Addendum 1.1: all tick paths have evidence.regime."""

    def _mk(self, tmp_path):
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

        calls = {"start": [], "stop": [], "stop_all": 0}
        router = SarvRouter(
            config=SarvRouterConfig(),
            start_bot=lambda s: calls["start"].append(s),
            stop_bot=lambda s: calls["stop"].append(s),
            stop_all=lambda: calls.__setitem__("stop_all", calls["stop_all"]+1),
            store=SarvStore(base_dir=tmp_path),
            audit=AuditTrail(base_dir=tmp_path),
        )
        return router, calls, _uptrend

    def test_kill_switch_has_regime_in_evidence(self, tmp_path):
        router, calls, _uptrend = self._mk(tmp_path)
        uid = "test-user-kill"
        router.tick(uid, _uptrend(300), now_idx=0)
        router.tick(uid, _uptrend(300), now_idx=router.config.stability_window)
        st = router.store.load(uid)
        st.kill_switch_manual = True
        router.store.save(uid, st)
        r = router.tick(uid, _uptrend(300), now_idx=router.config.stability_window + 1)
        assert r["action"] == "kill_switch_active"
        assert "evidence" in r
        assert r["evidence"]["regime"] == "uptrend"
        assert r["evidence"]["path"] == "kill_switch"

    def test_lifecycle_has_path_in_evidence(self, tmp_path):
        router, calls, _uptrend = self._mk(tmp_path)
        uid = "test-user-lifecycle"
        r = router.tick(uid, _uptrend(300), now_idx=0)
        assert "evidence" in r
        assert r["evidence"]["path"] == "lifecycle"
        assert r["evidence"]["regime"] == "uptrend"


class TestLastDecisionPersistence:
    """Phase 1c (ADR-0040 Addendum 1.1): persist last_decision for API/UI."""

    def test_sarv_state_has_last_decision_field(self):
        from app.services.bots.sarv_router.store import SarvState
        s = SarvState()
        assert hasattr(s, "last_decision")
        assert s.last_decision is None

    def test_sarv_state_roundtrip_preserves_last_decision(self, tmp_path):
        from app.services.bots.sarv_router.store import SarvState, SarvStore
        store = SarvStore(base_dir=tmp_path)
        s = SarvState()
        s.last_decision = {"why": "test", "confidence": 0.9, "tick_id": "x"}
        store.save("u1", s)
        loaded = store.load("u1")
        assert loaded.last_decision == {"why": "test", "confidence": 0.9, "tick_id": "x"}

    def test_tick_sets_state_last_decision(self, tmp_path):
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

        router = SarvRouter(
            config=SarvRouterConfig(),
            start_bot=lambda s: None,
            stop_bot=lambda s: None,
            stop_all=lambda: None,
            store=SarvStore(base_dir=tmp_path),
            audit=AuditTrail(base_dir=tmp_path),
        )
        router.tick("u-test", _uptrend(300), now_idx=0)
        st = router.store.load("u-test")
        assert st.last_decision is not None
        assert "why" in st.last_decision
        assert st.last_decision["evidence"]["path"] == "lifecycle"
