"""All 11 bots + archived flag in /bots/list and /bots/{slug}."""
import pytest
from fastapi.testclient import TestClient
from app.main import app

EXPECTED_ALL = {
    "nooaah", "sarv_router", "grid_bot", "market_scanner",
    "mean_revert", "trend_follow", "volatility_hunter",
    "volatility_hunter_v2", "smart_portfolio",
    "sarv_tiger", "scalp_master",
}
EXPECTED_ACTIVE = {"nooaah", "sarv_router"}


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


class TestBotsList:
    def test_includes_11(self, client):
        r = client.get("/v1/bots/list")
        assert r.status_code == 200
        data = r.json()
        slugs = {b["slug"] for b in data["items"]}
        assert slugs == EXPECTED_ALL, (
            f"missing: {EXPECTED_ALL - slugs}, extra: {slugs - EXPECTED_ALL}"
        )

    def test_archived_flag(self, client):
        r = client.get("/v1/bots/list")
        by = {b["slug"]: b for b in r.json()["items"]}
        for slug in EXPECTED_ACTIVE:
            assert by[slug]["archived"] is False, f"{slug} should be active"
        for slug in EXPECTED_ALL - EXPECTED_ACTIVE:
            assert by[slug]["archived"] is True, f"{slug} should be archived"


class TestGetBotInfo:
    def test_sarv_router_200(self, client):
        r = client.get("/v1/bots/sarv_router")
        assert r.status_code == 200, r.text[:200]
        assert r.json()["archived"] is False

    def test_sarv_tiger_stub(self, client):
        r = client.get("/v1/bots/sarv_tiger")
        assert r.status_code == 200, r.text[:200]
        assert r.json()["archived"] is True

    def test_nooaah_not_archived(self, client):
        r = client.get("/v1/bots/nooaah")
        assert r.json()["archived"] is False
