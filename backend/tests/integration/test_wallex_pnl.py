"""تست endpoint /v1/user/wallex/pnl + FIFO integration.

استراتژی: mock کردن WallexExchange.create تا get_orders و get_balances مجازی باشه.
"""

from __future__ import annotations

import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete

from app.core.auth import create_user_token
from app.domain.entities.balance import Balance
from app.domain.entities.order import Order
from app.domain.exceptions import ExchangeAuthError
from app.domain.value_objects.order_enums import (
    OrderSide,
    OrderStatus,
    OrderType,
)
from app.infrastructure.db.models.user import User
from app.infrastructure.db.session import SessionLocal, engine
from app.main import app


@pytest.fixture(autouse=True)
async def _dispose_engine_after_test():
    yield
    await engine.dispose()


@pytest.fixture
async def client():
    async with app.router.lifespan_context(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            yield c


@pytest.fixture
async def test_user_and_token():
    user_id = uuid.uuid4()
    email = f"pnl-{user_id.hex[:8]}@example.local"

    async with SessionLocal() as session:
        user = User(
            id=user_id,
            email=email,
            password_hash="test-hash-not-real",
        )
        session.add(user)
        await session.commit()

    token = create_user_token(str(user_id), email)

    yield {"user_id": user_id, "email": email, "token": token}

    async with SessionLocal() as session:
        await session.execute(delete(User).where(User.id == user_id))
        await session.commit()


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def make_order(
    symbol: str,
    side: OrderSide,
    qty: str,
    price: str,
    fee: str = "0",
    ts: int = 1000,
    status: OrderStatus = OrderStatus.FILLED,
) -> Order:
    q = Decimal(qty)
    p = Decimal(price)
    return Order(
        client_id=f"TEST-{ts}-{side}-{qty}",
        symbol=symbol,
        side=side,
        type=OrderType.LIMIT,
        status=status,
        price=p,
        stop_price=Decimal("0"),
        stop_price_condition="",
        orig_qty=q,
        executed_qty=q,
        executed_price=p,
        executed_sum=q * p,
        fee=Decimal(fee),
        active=False,
        executed_percent=Decimal("100"),
        created_at=ts,
        updated_at=ts,
    )


def make_balance(asset: str, available: str, locked: str = "0") -> Balance:
    a = Decimal(available)
    l = Decimal(locked)
    return Balance(
        asset=asset,
        available=a,
        locked=l,
        total=max(a, l),  # per fix mapper.py
        fa_name=None,
        en_name=None,
    )


def make_mock_exchange(orders=None, balances=None, error=None):
    mock_ex = MagicMock()
    mock_ex.aclose = AsyncMock()
    if error:
        mock_ex.get_orders = AsyncMock(side_effect=error)
        mock_ex.get_balances = AsyncMock(side_effect=error)
    else:
        mock_ex.get_orders = AsyncMock(return_value=orders or [])
        mock_ex.get_balances = AsyncMock(return_value=balances or [])
    return mock_ex


# ─────────────────────────────────────────
# Tests
# ─────────────────────────────────────────

class TestAuth:
    async def test_pnl_without_token(self, client) -> None:
        r = await client.get("/v1/user/wallex/pnl")
        assert r.status_code == 401

    async def test_pnl_with_valid_token(
        self, client, test_user_and_token
    ) -> None:
        # بدون Wallex connected → 400 not_connected
        r = await client.get(
            "/v1/user/wallex/pnl",
            headers=auth_headers(test_user_and_token["token"]),
        )
        assert r.status_code == 400
        assert r.json()["detail"]["code"] == "not_connected"


class TestPnLBasic:
    async def test_empty_orders_empty_pnl(
        self, client, test_user_and_token
    ) -> None:
        """کاربر با Wallex متصل ولی بدون سفارش."""
        # اول connect (فقط برای ذخیره‌ی توکن)
        mock_connect = make_mock_exchange(balances=[make_balance("TMN", "100")])
        with patch(
            "app.services.wallex.service.WallexExchange.create",
            return_value=mock_connect,
        ):
            await client.post(
                "/v1/user/wallex/connect",
                headers=auth_headers(test_user_and_token["token"]),
                json={"token": "valid-token-1234567890"},
            )

        # حالا pnl
        mock_pnl = make_mock_exchange(orders=[], balances=[])
        with patch(
            "app.services.wallex.service.WallexExchange.create",
            return_value=mock_pnl,
        ):
            r = await client.get(
                "/v1/user/wallex/pnl",
                headers=auth_headers(test_user_and_token["token"]),
            )

        assert r.status_code == 200
        d = r.json()
        assert d["assets"] == []
        assert d["summary"]["total_pnl"] == "0"

    async def test_simple_buy_pnl(
        self, client, test_user_and_token
    ) -> None:
        """خرید 100 @ 10، قیمت فعلی 12 → PnL = 200 (+20%)."""
        # connect
        mock_connect = make_mock_exchange(balances=[])
        with patch(
            "app.services.wallex.service.WallexExchange.create",
            return_value=mock_connect,
        ):
            await client.post(
                "/v1/user/wallex/connect",
                headers=auth_headers(test_user_and_token["token"]),
                json={"token": "valid-token-1234567890"},
            )

        # pnl
        orders = [
            make_order("PEPETMN", OrderSide.BUY, "100", "10"),
        ]
        balances = [make_balance("PEPE", "100")]
        mock_pnl = make_mock_exchange(orders=orders, balances=balances)
        with patch(
            "app.services.wallex.service.WallexExchange.create",
            return_value=mock_pnl,
        ):
            r = await client.get(
                "/v1/user/wallex/pnl",
                headers=auth_headers(test_user_and_token["token"]),
            )

        assert r.status_code == 200
        d = r.json()
        assert len(d["assets"]) == 1
        asset = d["assets"][0]
        assert asset["asset"] == "PEPE"
        assert asset["avg_cost"] == "10"
        assert asset["total_cost"] == "1000"
        assert asset["has_unknown_history"] is False


class TestPnLFIFO:
    async def test_fifo_consumes_oldest_first(
        self, client, test_user_and_token
    ) -> None:
        """خرید 100 @ 10، خرید 100 @ 20، فروش 100 → باقی: 100 @ 20."""
        # connect
        mock_connect = make_mock_exchange(balances=[])
        with patch(
            "app.services.wallex.service.WallexExchange.create",
            return_value=mock_connect,
        ):
            await client.post(
                "/v1/user/wallex/connect",
                headers=auth_headers(test_user_and_token["token"]),
                json={"token": "valid-token-1234567890"},
            )

        orders = [
            make_order("PEPETMN", OrderSide.BUY, "100", "10", ts=1000),
            make_order("PEPETMN", OrderSide.BUY, "100", "20", ts=2000),
            make_order("PEPETMN", OrderSide.SELL, "100", "25", ts=3000),
        ]
        balances = [make_balance("PEPE", "100")]
        mock_pnl = make_mock_exchange(orders=orders, balances=balances)
        with patch(
            "app.services.wallex.service.WallexExchange.create",
            return_value=mock_pnl,
        ):
            r = await client.get(
                "/v1/user/wallex/pnl",
                headers=auth_headers(test_user_and_token["token"]),
            )

        assert r.status_code == 200
        asset = r.json()["assets"][0]
        assert asset["avg_cost"] == "20"  # FIFO، نه 15


class TestPnLUnknownHistory:
    async def test_balance_without_order_is_unknown(
        self, client, test_user_and_token
    ) -> None:
        """موجودی داره ولی سفارشی نیست (خرید قبل از تاریخچه)."""
        # connect
        mock_connect = make_mock_exchange(balances=[])
        with patch(
            "app.services.wallex.service.WallexExchange.create",
            return_value=mock_connect,
        ):
            await client.post(
                "/v1/user/wallex/connect",
                headers=auth_headers(test_user_and_token["token"]),
                json={"token": "valid-token-1234567890"},
            )

        # balance داره ولی orders خالی
        balances = [make_balance("BTC", "0.1")]
        mock_pnl = make_mock_exchange(orders=[], balances=balances)
        with patch(
            "app.services.wallex.service.WallexExchange.create",
            return_value=mock_pnl,
        ):
            r = await client.get(
                "/v1/user/wallex/pnl",
                headers=auth_headers(test_user_and_token["token"]),
            )

        assert r.status_code == 200
        d = r.json()
        btc_asset = next(a for a in d["assets"] if a["asset"] == "BTC")
        assert btc_asset["has_unknown_history"] is True
        assert btc_asset["unrealized_pnl"] is None
        assert d["summary"]["assets_with_unknown_history"] >= 1


class TestPnLErrors:
    async def test_auth_error_from_wallex(
        self, client, test_user_and_token
    ) -> None:
        """Wallex 401 → 400 invalid_token."""
        # connect
        mock_connect = make_mock_exchange(balances=[])
        with patch(
            "app.services.wallex.service.WallexExchange.create",
            return_value=mock_connect,
        ):
            await client.post(
                "/v1/user/wallex/connect",
                headers=auth_headers(test_user_and_token["token"]),
                json={"token": "valid-token-1234567890"},
            )

        # pnl با auth error
        mock_pnl = make_mock_exchange(error=ExchangeAuthError("401"))
        with patch(
            "app.services.wallex.service.WallexExchange.create",
            return_value=mock_pnl,
        ):
            r = await client.get(
                "/v1/user/wallex/pnl",
                headers=auth_headers(test_user_and_token["token"]),
            )

        assert r.status_code == 400
        assert r.json()["detail"]["code"] == "invalid_token"
