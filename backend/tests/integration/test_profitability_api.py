"""Integration tests for profitability API."""

from decimal import Decimal
from typing import Any

import pytest

from app.main import app
from app.presentation.api.deps import get_exchange


class FakeExchange:
    """Fake exchange that returns a deterministic order book."""

    def __init__(self, best_bid: str, best_ask: str) -> None:
        self._best_bid = best_bid
        self._best_ask = best_ask
        self.calls: list[str] = []

    async def get_order_book(self, symbol: str) -> dict[str, Any]:
        self.calls.append(symbol)
        # Mimic the raw Wallex structure that map_order_book expects.
        return {
            "result": {
                "ask": [{"price": self._best_ask, "quantity": "1000", "sum": "0"}],
                "bid": [{"price": self._best_bid, "quantity": "1000", "sum": "0"}],
            }
        }

    # Protocol stubs (not used in these tests)
    async def get_markets(self):  # pragma: no cover
        return []

    async def get_market(self, symbol: str):  # pragma: no cover
        raise NotImplementedError

    async def get_balances(self):  # pragma: no cover
        return []

    async def health_check(self) -> bool:  # pragma: no cover
        return True


@pytest.fixture
def fake_exchange_factory():
    """Returns a helper to install a FakeExchange for a test and clean up after."""

    def install(best_bid: str, best_ask: str) -> FakeExchange:
        fake = FakeExchange(best_bid=best_bid, best_ask=best_ask)
        app.dependency_overrides[get_exchange] = lambda: fake
        return fake

    yield install

    # cleanup
    app.dependency_overrides.pop(get_exchange, None)


# ---------- /evaluate (real order book via mocked exchange) ----------


class TestEvaluateWithRealOrderBook:
    def test_profitable_scenario(self, client, fake_exchange_factory):
        fake = fake_exchange_factory(best_bid="100", best_ask="101")
        r = client.post(
            "/v1/profitability/evaluate",
            json={
                "symbol": "XRPTMN",
                "order_type": "maker",
                "capital": 1000000,
            },
        )
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["is_profitable"] is True
        assert data["best_bid"] == "100.00000000"
        assert data["best_ask"] == "101.00000000"
        assert fake.calls == ["XRPTMN"]

    def test_unprofitable_scenario(self, client, fake_exchange_factory):
        fake_exchange_factory(best_bid="384188", best_ask="384369")
        r = client.post(
            "/v1/profitability/evaluate",
            json={
                "symbol": "XRPTMN",
                "order_type": "maker",
                "capital": 1000000,
                "maker_fee_rate": 0.01,
            },
        )
        assert r.status_code == 200
        assert r.json()["is_profitable"] is False

    def test_symbol_passed_to_exchange(self, client, fake_exchange_factory):
        fake = fake_exchange_factory(best_bid="100", best_ask="101")
        client.post(
            "/v1/profitability/evaluate",
            json={
                "symbol": "BTCUSDT",
                "order_type": "taker",
                "capital": 500000,
            },
        )
        assert fake.calls == ["BTCUSDT"]

    def test_exchange_failure_returns_502(self, client):
        class BrokenExchange(FakeExchange):
            async def get_order_book(self, symbol: str):
                raise RuntimeError("network down")

        app.dependency_overrides[get_exchange] = lambda: BrokenExchange("100", "101")
        try:
            r = client.post(
                "/v1/profitability/evaluate",
                json={
                    "symbol": "XRPTMN",
                    "order_type": "maker",
                    "capital": 1000000,
                },
            )
            assert r.status_code == 502
            assert "network down" in r.json()["detail"]
        finally:
            app.dependency_overrides.pop(get_exchange, None)

    def test_validation_still_enforced(self, client, fake_exchange_factory):
        fake_exchange_factory(best_bid="100", best_ask="101")
        r = client.post(
            "/v1/profitability/evaluate",
            json={"symbol": "XRPTMN", "order_type": "maker"},  # missing capital
        )
        assert r.status_code == 422


# ---------- /evaluate-with-snapshot (no exchange needed) ----------


class TestEvaluateWithSnapshot:
    def test_profitable_scenario(self, client):
        r = client.post(
            "/v1/profitability/evaluate-with-snapshot",
            params={"best_bid": 100.0, "best_ask": 101.0},
            json={
                "symbol": "XRPTMN",
                "order_type": "maker",
                "capital": 1000000,
            },
        )
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["symbol"] == "XRPTMN"
        assert data["order_type"] == "maker"
        assert data["is_profitable"] is True
        assert Decimal(data["net_profit"]) > 0
        assert data["best_bid"] == "100.00000000"
        assert data["best_ask"] == "101.00000000"

    def test_unprofitable_scenario(self, client):
        r = client.post(
            "/v1/profitability/evaluate-with-snapshot",
            params={"best_bid": 100.0, "best_ask": 100.01},
            json={
                "symbol": "XRPTMN",
                "order_type": "maker",
                "capital": 1000000,
                "maker_fee_rate": 0.01,
            },
        )
        assert r.status_code == 200
        assert r.json()["is_profitable"] is False

    def test_missing_capital_returns_422(self, client):
        r = client.post(
            "/v1/profitability/evaluate-with-snapshot",
            params={"best_bid": 100.0, "best_ask": 101.0},
            json={"symbol": "XRPTMN", "order_type": "maker"},
        )
        assert r.status_code == 422

    def test_negative_capital_returns_422(self, client):
        r = client.post(
            "/v1/profitability/evaluate-with-snapshot",
            params={"best_bid": 100.0, "best_ask": 101.0},
            json={"symbol": "XRPTMN", "order_type": "maker", "capital": -1000},
        )
        assert r.status_code == 422

    def test_invalid_order_type_returns_422(self, client):
        r = client.post(
            "/v1/profitability/evaluate-with-snapshot",
            params={"best_bid": 100.0, "best_ask": 101.0},
            json={"symbol": "XRPTMN", "order_type": "invalid", "capital": 1000},
        )
        assert r.status_code == 422

    def test_negative_bid_returns_400(self, client):
        r = client.post(
            "/v1/profitability/evaluate-with-snapshot",
            params={"best_bid": -1.0, "best_ask": 100.0},
            json={"symbol": "XRPTMN", "order_type": "maker", "capital": 1000},
        )
        assert r.status_code == 400

    def test_ask_below_bid_returns_400(self, client):
        r = client.post(
            "/v1/profitability/evaluate-with-snapshot",
            params={"best_bid": 100.0, "best_ask": 99.0},
            json={"symbol": "XRPTMN", "order_type": "maker", "capital": 1000},
        )
        assert r.status_code == 400
