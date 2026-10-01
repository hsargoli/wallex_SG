"""Integration tests for candles API."""

from decimal import Decimal
from typing import Any

import pytest

from app.domain.entities.candle import Candle
from app.main import app
from app.presentation.api.deps import get_exchange


class FakeExchange:
    """Fake exchange returning deterministic candles."""

    def __init__(self, candles: list[Candle] | None = None) -> None:
        self._candles = candles or []
        self.calls: list[dict[str, Any]] = []

    async def get_candles(
        self,
        symbol: str,
        resolution: str,
        from_ts: int,
        to_ts: int,
    ) -> list[Candle]:
        self.calls.append(
            {
                "symbol": symbol,
                "resolution": resolution,
                "from_ts": from_ts,
                "to_ts": to_ts,
            }
        )
        return list(self._candles)

    # ---- Protocol stubs ----
    async def get_markets(self):  # pragma: no cover
        return []

    async def get_market(self, symbol: str):  # pragma: no cover
        raise NotImplementedError

    async def get_balances(self):  # pragma: no cover
        return []

    async def get_order_book(self, symbol: str):  # pragma: no cover
        return {}

    async def health_check(self) -> bool:  # pragma: no cover
        return True


def _make_candles(n: int, step_sec: int = 60) -> list[Candle]:
    return [
        Candle(
            time=1000 + i * step_sec,
            open=Decimal(100 + i),
            high=Decimal(105 + i),
            low=Decimal(95 + i),
            close=Decimal(102 + i),
            volume=Decimal("1.5"),
        )
        for i in range(n)
    ]


@pytest.fixture
def fake_exchange_factory():
    def install(candles: list[Candle]) -> FakeExchange:
        fake = FakeExchange(candles=candles)
        app.dependency_overrides[get_exchange] = lambda: fake
        return fake

    yield install
    app.dependency_overrides.pop(get_exchange, None)


class TestCandlesEndpoint:
    def test_1h_returns_candles(self, client, fake_exchange_factory):
        # ۶۰ کندل ۱ ساعته (والکس مستقیم میده)
        candles = _make_candles(60, step_sec=3600)
        fake = fake_exchange_factory(candles)

        r = client.get("/v1/markets/candles/BTCTMN?tf=1h&limit=10")
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["symbol"] == "BTCTMN"
        assert data["timeframe"] == "1h"
        # آخرین ۱۰ تا
        assert data["count"] == 10
        assert len(data["candles"]) == 10
        # resolution والکس برای 1h باید "60" باشه
        assert fake.calls[0]["resolution"] == "60"

    def test_4h_aggregates_1h(self, client, fake_exchange_factory):
        # ۸ کندل ۱ ساعته → باید ۲ تا ۴ ساعته بشه
        candles = _make_candles(8, step_sec=3600)
        fake = fake_exchange_factory(candles)

        r = client.get("/v1/markets/candles/BTCTMN?tf=4h&limit=10")
        assert r.status_code == 200
        data = r.json()
        assert data["count"] == 2
        # resolution باید 60 باشه (1h که ادغام میشه)
        assert fake.calls[0]["resolution"] == "60"

    def test_15m_aggregates_1m(self, client, fake_exchange_factory):
        # ۳۰ کندل ۱ دقیقه‌ای → ۲ تا ۱۵ دقیقه‌ای
        candles = _make_candles(30, step_sec=60)
        fake = fake_exchange_factory(candles)

        r = client.get("/v1/markets/candles/BTCTMN?tf=15m&limit=10")
        assert r.status_code == 200
        data = r.json()
        assert data["count"] == 2
        # resolution والکس برای 1m باید "15" باشه (عجیبه ولی والکس اینطوریه)
        assert fake.calls[0]["resolution"] == "15"

    def test_1D_returns_daily(self, client, fake_exchange_factory):
        candles = _make_candles(5, step_sec=86400)
        fake = fake_exchange_factory(candles)

        r = client.get("/v1/markets/candles/BTCTMN?tf=1D&limit=5")
        assert r.status_code == 200
        data = r.json()
        assert data["count"] == 5
        assert fake.calls[0]["resolution"] == "D"

    def test_invalid_timeframe_returns_400(self, client, fake_exchange_factory):
        fake_exchange_factory([])
        r = client.get("/v1/markets/candles/BTCTMN?tf=7m&limit=10")
        assert r.status_code == 400
        assert "Unsupported timeframe" in r.json()["detail"]

    def test_limit_out_of_range_returns_400(self, client, fake_exchange_factory):
        fake_exchange_factory([])
        r = client.get("/v1/markets/candles/BTCTMN?tf=1h&limit=3500")
        assert r.status_code == 400
        assert "limit" in r.json()["detail"].lower()

    def test_zero_limit_returns_400(self, client, fake_exchange_factory):
        fake_exchange_factory([])
        r = client.get("/v1/markets/candles/BTCTMN?tf=1h&limit=0")
        assert r.status_code == 400

    def test_empty_candles_returns_empty_list(self, client, fake_exchange_factory):
        fake_exchange_factory([])
        r = client.get("/v1/markets/candles/BTCTMN?tf=1h&limit=10")
        assert r.status_code == 200
        assert r.json()["count"] == 0
        assert r.json()["candles"] == []

    def test_symbol_passed_to_exchange(self, client, fake_exchange_factory):
        candles = _make_candles(5, step_sec=3600)
        fake = fake_exchange_factory(candles)

        client.get("/v1/markets/candles/XRPTMN?tf=1h&limit=5")
        assert fake.calls[0]["symbol"] == "XRPTMN"

    def test_candle_format(self, client, fake_exchange_factory):
        candles = _make_candles(1, step_sec=3600)
        fake_exchange_factory(candles)

        r = client.get("/v1/markets/candles/BTCTMN?tf=1h&limit=1")
        c = r.json()["candles"][0]
        # همه فیلدها باید string باشن (Decimal → string)
        assert isinstance(c["time"], int)
        assert isinstance(c["open"], str)
        assert isinstance(c["high"], str)
        assert isinstance(c["low"], str)
        assert isinstance(c["close"], str)
        assert isinstance(c["volume"], str)
