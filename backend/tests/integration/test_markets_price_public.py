"""Public price endpoint — no auth required (per Hosein 2026-10-31)."""
import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


class TestPublicPrice:
    def test_no_auth_required(self, client):
        """GET /v1/markets/price/{symbol} must work without any token."""
        r = client.get("/v1/markets/price/BTCTMN")
        assert r.status_code == 200, r.text[:200]

    def test_returns_symbol_and_price(self, client):
        r = client.get("/v1/markets/price/BTCTMN")
        data = r.json()
        assert "symbol" in data
        assert data["symbol"] == "BTCTMN"
        assert "price" in data

    def test_invalid_symbol_returns_null_price(self, client):
        r = client.get("/v1/markets/price/NONEXISTENT999TMN")
        assert r.status_code == 200
        data = r.json()
        assert data["price"] is None
        assert "error" in data

    def test_works_with_guest_token_too(self, client):
        """Guest token must not break (it should just be ignored)."""
        r = client.get(
            "/v1/markets/price/BTCTMN",
            headers={"X-Guest-Token": "00000000-0000-0000-0000-000000000000"},
        )
        assert r.status_code == 200
