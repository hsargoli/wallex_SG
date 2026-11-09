"""Phase 4 MVP: API tests for /feedback (ADR-0043)."""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.presentation.api.v1 import sarvrouter
import json

client = TestClient(app)

@pytest.fixture
def mock_state(tmp_path, monkeypatch):
    # Redirect SARV_DIR to tmp_path
    monkeypatch.setattr(sarvrouter, "SARV_DIR", tmp_path)
    users_dir = tmp_path / "users"
    users_dir.mkdir(parents=True)
    
    # Create a fake state with last_decision
    state = {
        "current_regime": "uptrend",
        "last_decision": {"tick_id": "tick-123", "action": "switched"},
        "kill_switch_manual": False,
        "kill_switch_auto": False
    }
    (users_dir / "production-default.json").write_text(json.dumps(state))
    return tmp_path

def test_post_feedback_accept(mock_state):
    resp = client.post("/v1/sarvrouter/feedback", json={"tick_id": "tick-123", "user_choice": "accept"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    
    # Verify file written
    feedback_file = mock_state / "users" / "production-default.feedback.jsonl"
    assert feedback_file.exists()

def test_post_feedback_mismatch(mock_state):
    resp = client.post("/v1/sarvrouter/feedback", json={"tick_id": "wrong-tick", "user_choice": "reject"})
    assert resp.status_code == 409
    assert "mismatch" in resp.json()["detail"].lower()

def test_post_feedback_no_last_decision(tmp_path, monkeypatch):
    monkeypatch.setattr(sarvrouter, "SARV_DIR", tmp_path)
    users_dir = tmp_path / "users"
    users_dir.mkdir(parents=True)
    (users_dir / "production-default.json").write_text(json.dumps({}))
    
    resp = client.post("/v1/sarvrouter/feedback", json={"tick_id": "x", "user_choice": "accept"})
    assert resp.status_code == 503
