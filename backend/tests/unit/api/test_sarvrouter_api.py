"""SarvRouter API — status + kill switch (TDD RED first)."""
import json
import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    """Isolate to tmp dir so tests don't touch real data."""
    # Patch the path constants used by the endpoint
    import app.presentation.api.v1.sarvrouter as sr
    monkeypatch.setattr(sr, "SARV_DIR", tmp_path)
    # Seed minimal state
    (tmp_path / "users").mkdir()
    (tmp_path / "users" / "production-default.json").write_text(json.dumps({
        "total_capital": 1_000_000.0,
        "current_regime": "unknown",
        "active_bots": [],
        "allocations": {},
        "cash": 1_000_000.0,
        "last_switch_idx": None,
        "regime_since_idx": None,
        "daily_pnl_pct": 0.0,
        "daily_reset_day": "",
        "kill_switch_manual": False,
        "kill_switch_auto": False,
    }))
    (tmp_path / "gate.json").write_text(json.dumps({
        "allow_new_entries": True,
        "regime": "unknown",
        "updated_at": "2026-10-30T00:00:00+00:00",
    }))
    return TestClient(app), tmp_path


class TestSarvRouterStatus:
    def test_status_200(self, client):
        c, _ = client
        r = c.get("/v1/sarvrouter/status")
        assert r.status_code == 200, r.text[:200]

    def test_status_has_regime_and_gate(self, client):
        c, _ = client
        r = c.get("/v1/sarvrouter/status")
        data = r.json()
        assert "regime" in data
        assert "gate" in data
        assert "allow_new_entries" in data["gate"]


class TestKillSwitch:
    def test_kill_switch_sets_both_flags(self, client):
        c, tmp_path = client
        r = c.post("/v1/sarvrouter/kill-switch")
        assert r.status_code == 200, r.text[:300]
        # Check state file
        state = json.loads((tmp_path / "users" / "production-default.json").read_text())
        assert state["kill_switch_manual"] is True
        # Check gate file
        gate = json.loads((tmp_path / "gate.json").read_text())
        assert gate["allow_new_entries"] is False

    def test_reenable_after_kill(self, client):
        c, tmp_path = client
        c.post("/v1/sarvrouter/kill-switch")
        r = c.post("/v1/sarvrouter/reenable")
        assert r.status_code == 200
        state = json.loads((tmp_path / "users" / "production-default.json").read_text())
        assert state["kill_switch_manual"] is False
        gate = json.loads((tmp_path / "gate.json").read_text())
        assert gate["allow_new_entries"] is True
