"""Guard: /v1/bots/{slug} must include backtest + paper + meta (TDD RED)."""
import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


class TestGetBotInfoExtended:
    def test_nooaah_not_404(self, client):
        """nooaah is scheduler-based, not in registry — must not 404."""
        r = client.get("/v1/bots/nooaah")
        assert r.status_code == 200, f"got {r.status_code}: {r.text[:200]}"

    def test_nooaah_includes_backtest_paper_meta(self, client):
        r = client.get("/v1/bots/nooaah")
        assert r.status_code == 200
        data = r.json()
        for key in ("backtest", "paper", "meta"):
            assert key in data, f"missing '{key}', keys={list(data.keys())}"

    def test_nooaah_paper_has_status(self, client):
        r = client.get("/v1/bots/nooaah")
        data = r.json()
        assert "status" in data["paper"], f"paper keys: {list(data['paper'].keys())}"

    def test_unknown_slug_404(self, client):
        r = client.get("/v1/bots/nonexistent_bot_xyz")
        assert r.status_code == 404
