"""E2E smoke: guest flow per Hosein 2026-10-30 decision."""
import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


class TestGuestFlow:
    def test_1_create_guest(self, client):
        r = client.post("/v1/guest/anonymous")
        assert r.status_code == 200, r.text[:200]
        data = r.json()
        assert "guest_token" in data
        assert data["capital_total"] == 100_000.0, f"expected 100k, got {data['capital_total']}"

    def test_2_guest_sees_11_bots(self, client):
        # create guest first
        r0 = client.post("/v1/guest/anonymous")
        token = r0.json()["guest_token"]

        r = client.get("/v1/bots/list", headers={"X-Guest-Token": token})
        assert r.status_code == 200
        items = r.json()["items"]
        assert len(items) == 11, f"expected 11, got {len(items)}"

        by = {i["slug"]: i for i in items}
        # Only 2 active
        active = [s for s, i in by.items() if not i["archived"]]
        assert set(active) == {"nooaah", "sarv_router"}, f"active: {active}"

    def test_3_nooaah_view_works(self, client):
        r = client.get("/v1/bots/nooaah")
        assert r.status_code == 200
        assert r.json()["archived"] is False

    def test_4_archived_bot_shows_true(self, client):
        r = client.get("/v1/bots/grid_bot")
        assert r.status_code == 200
        assert r.json()["archived"] is True

    def test_5_guest_paper_start(self, client):
        """Guest start paper — uses 100k capital."""
        r0 = client.post("/v1/guest/anonymous")
        token = r0.json()["guest_token"]
        r = client.post(
            "/v1/guest/paper-v3/start",
            headers={"X-Guest-Token": token},
            json={"bot_slug": "nooaah", "initial_capital": 100_000},
        )
        assert r.status_code == 200, r.text[:300]
