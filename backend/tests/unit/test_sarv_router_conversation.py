"""Phase 3 MVP: ConversationEngine tests (ADR-0042)."""
import pytest
from app.services.bots.sarv_router.conversation import ConversationEngine


class TestConversationEngine:
    def test_pending_explanation(self):
        decision = {
            "action": "pending",
            "why": "stability_window",
            "evidence": {"regime": "uptrend", "stable_candles": 12, "needed": 36},
            "confidence": 0.8,
        }
        answer = ConversationEngine.explain(decision)
        assert "منتظر" in answer or "پایدار" in answer

    def test_switched_explanation(self):
        decision = {
            "action": "switched",
            "why": "lifecycle_switch",
            "evidence": {"regime": "uptrend", "active_bots": ["nooaah"]},
            "confidence": 0.95,
        }
        answer = ConversationEngine.explain(decision)
        assert "روند" in answer or "تغییر" in answer or "فعال" in answer

    def test_kill_switch_explanation(self):
        decision = {
            "action": "kill_switch_active",
            "why": "kill_switch_manual",
            "evidence": {"reason": "manual", "regime": "uptrend"},
            "confidence": 1.0,
        }
        answer = ConversationEngine.explain(decision)
        assert "توقف" in answer or "متوقف" in answer

    def test_daily_loss_explanation(self):
        decision = {
            "action": "daily_loss_kill",
            "why": "daily_loss=-2.1",
            "evidence": {"daily_pnl_pct": -2.1, "regime": "uptrend"},
            "confidence": 1.0,
        }
        answer = ConversationEngine.explain(decision)
        assert "ضرر" in answer or "حد" in answer

    def test_unknown_action_fallback(self):
        decision = {
            "action": "some_weird_action",
            "why": "?",
            "evidence": {},
            "confidence": 0.5,
        }
        answer = ConversationEngine.explain(decision)
        assert "نمی‌دانم" in answer or "نامشخص" in answer or "اطلاع" in answer
