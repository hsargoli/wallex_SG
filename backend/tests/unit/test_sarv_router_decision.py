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
