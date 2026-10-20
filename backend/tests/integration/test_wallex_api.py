"""تست endpointهای /v1/user/wallex/*.

استراتژی: mock کردن WallexExchange.create تا واقعاً به والکس وصل نشیم.
اعتبارسنجی توکن، رمزنگاری، و ذخیره در DB واقعاً تست می‌شن.
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
from app.domain.exceptions import ExchangeAuthError
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
    email = f"wallex-{user_id.hex[:8]}@example.local"

    import bcrypt as _bcrypt
    real_hash = _bcrypt.hashpw(b"TestPass123!@#", _bcrypt.gensalt()).decode("utf-8")

    async with SessionLocal() as session:
        user = User(
            id=user_id,
            email=email,
            password_hash=real_hash,
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


def make_balance(asset: str, available: str, locked: str = "0") -> Balance:
    return Balance(
        asset=asset,
        available=Decimal(available),
        locked=Decimal(locked),
        total=Decimal(available) + Decimal(locked),
        fa_name=None,
        en_name=None,
    )


def make_mock_exchange(balances=None, error=None):
    """Mock WallexExchange که create() یه instance با get_balances مجازی می‌ده."""
    mock_ex = MagicMock()
    mock_ex.aclose = AsyncMock()
    if error:
        mock_ex.get_balances = AsyncMock(side_effect=error)
    else:
        mock_ex.get_balances = AsyncMock(
            return_value=balances or [make_balance("TMN", "5000000")]
        )
    return mock_ex


class TestAuth:
    async def test_connect_without_token(self, client) -> None:
        r = await client.post("/v1/user/wallex/connect", json={"token": "x" * 20})
        assert r.status_code == 401

    async def test_status_without_token(self, client) -> None:
        r = await client.get("/v1/user/wallex/status")
        assert r.status_code == 401

    async def test_disconnect_without_token(self, client) -> None:
        r = await client.delete("/v1/user/wallex/disconnect")
        assert r.status_code == 401


class TestStatusDisconnected:
    async def test_status_when_not_connected(
        self, client, test_user_and_token
    ) -> None:
        r = await client.get(
            "/v1/user/wallex/status",
            headers=auth_headers(test_user_and_token["token"]),
        )
        assert r.status_code == 200
        d = r.json()
        assert d["connected"] is False
        assert d["connected_at"] is None
        assert d["balances"] is None


class TestConnect:
    async def test_connect_success(
        self, client, test_user_and_token
    ) -> None:
        """connect با توکن معتبر → ذخیره + برگشت موجودی."""
        mock_ex = make_mock_exchange(
            balances=[make_balance("TMN", "5000000"), make_balance("BTC", "0.01")]
        )
        with patch(
            "app.services.wallex.service.WallexExchange.create",
            return_value=mock_ex,
        ):
            r = await client.post(
                "/v1/user/wallex/connect",
                headers=auth_headers(test_user_and_token["token"]),
                json={"token": "valid-wallex-token-12345", "password": "TestPass123!@#"},
            )
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["connected"] is True
        assert d["connected_at"] is not None
        assert len(d["balances"]) == 2
        assert d["balances"][0]["asset"] == "TMN"

    async def test_connect_invalid_token(
        self, client, test_user_and_token
    ) -> None:
        """connect با توکن نامعتبر → 400 invalid_token."""
        mock_ex = make_mock_exchange(error=ExchangeAuthError("401"))
        with patch(
            "app.services.wallex.service.WallexExchange.create",
            return_value=mock_ex,
        ):
            r = await client.post(
                "/v1/user/wallex/connect",
                headers=auth_headers(test_user_and_token["token"]),
                json={"token": "invalid-token-123456", "password": "TestPass123!@#"},
            )
        assert r.status_code == 400
        assert r.json()["detail"]["code"] == "invalid_token"

    async def test_connect_short_token_rejected(
        self, client, test_user_and_token
    ) -> None:
        """توکن کوتاه (< 10) → 422 (pydantic validation)."""
        r = await client.post(
            "/v1/user/wallex/connect",
            headers=auth_headers(test_user_and_token["token"]),
            json={"token": "short", "password": "TestPass123!@#"},
        )
        assert r.status_code == 422

    async def test_connect_then_status_shows_balances(
        self, client, test_user_and_token
    ) -> None:
        """connect → status → موجودی‌ها نشون داده می‌شن."""
        balances = [make_balance("TMN", "7000000")]
        mock_ex_connect = make_mock_exchange(balances=balances)
        mock_ex_status = make_mock_exchange(balances=balances)

        with patch(
            "app.services.wallex.service.WallexExchange.create",
            side_effect=[mock_ex_connect, mock_ex_status],
        ):
            await client.post(
                "/v1/user/wallex/connect",
                headers=auth_headers(test_user_and_token["token"]),
                json={"token": "valid-token-12345", "password": "TestPass123!@#"},
            )
            r = await client.get(
                "/v1/user/wallex/status",
                headers=auth_headers(test_user_and_token["token"]),
            )

        assert r.status_code == 200
        d = r.json()
        assert d["connected"] is True
        assert d["balances"] is not None
        assert d["balances"][0]["asset"] == "TMN"
        assert d["balances"][0]["available"] == "7000000"


class TestDisconnect:
    async def test_disconnect_when_not_connected(
        self, client, test_user_and_token
    ) -> None:
        """disconnect وقتی وصل نیست → 200، idempotent."""
        r = await client.delete(
            "/v1/user/wallex/disconnect",
            headers=auth_headers(test_user_and_token["token"]),
        )
        assert r.status_code == 200
        assert r.json()["connected"] is False

    async def test_disconnect_after_connect(
        self, client, test_user_and_token
    ) -> None:
        """connect → disconnect → status disconnected."""
        mock_ex = make_mock_exchange()
        with patch(
            "app.services.wallex.service.WallexExchange.create",
            return_value=mock_ex,
        ):
            await client.post(
                "/v1/user/wallex/connect",
                headers=auth_headers(test_user_and_token["token"]),
                json={"token": "valid-token-12345", "password": "TestPass123!@#"},
            )

        r = await client.delete(
            "/v1/user/wallex/disconnect",
            headers=auth_headers(test_user_and_token["token"]),
        )
        assert r.status_code == 200
        assert r.json()["connected"] is False

        # status
        r2 = await client.get(
            "/v1/user/wallex/status",
            headers=auth_headers(test_user_and_token["token"]),
        )
        assert r2.json()["connected"] is False


# ═══════════════════════════════════════════════════════════════
# Fix #3.5 — Password confirmation regression tests
# ═══════════════════════════════════════════════════════════════

class TestPasswordConfirmation:
    """Regression: password required on /connect and /connect-trade."""

    async def test_connect_without_password_422(self, client, test_user_and_token) -> None:
        r = await client.post(
            "/v1/user/wallex/connect",
            headers=auth_headers(test_user_and_token["token"]),
            json={"token": "valid-token-12345"},
        )
        assert r.status_code == 422, r.text
        assert "password" in str(r.json()).lower()

    async def test_connect_wrong_password_401(self, client, test_user_and_token) -> None:
        r = await client.post(
            "/v1/user/wallex/connect",
            headers=auth_headers(test_user_and_token["token"]),
            json={"token": "valid-token-12345", "password": "WrongPassword!@#"},
        )
        assert r.status_code == 401, r.text
        assert "رمز" in r.text or "password" in r.text.lower()

    async def test_connect_correct_password_200(self, client, test_user_and_token) -> None:
        mock_ex = make_mock_exchange(balances=[make_balance("TMN", "100")])
        with patch(
            "app.services.wallex.service.WallexExchange.create",
            return_value=mock_ex,
        ):
            r = await client.post(
                "/v1/user/wallex/connect",
                headers=auth_headers(test_user_and_token["token"]),
                json={"token": "valid-token-12345", "password": "TestPass123!@#"},
            )
        assert r.status_code == 200, r.text

    async def test_connect_trade_without_password_422(self, client, test_user_and_token) -> None:
        r = await client.post(
            "/v1/user/wallex/connect-trade",
            headers=auth_headers(test_user_and_token["token"]),
            json={"trade_token": "valid-trade-token-12345"},
        )
        assert r.status_code == 422, r.text
        assert "password" in str(r.json()).lower()

    async def test_connect_trade_wrong_password_401(self, client, test_user_and_token) -> None:
        r = await client.post(
            "/v1/user/wallex/connect-trade",
            headers=auth_headers(test_user_and_token["token"]),
            json={"trade_token": "valid-trade-token-12345", "password": "WrongPassword!@#"},
        )
        assert r.status_code == 401, r.text
        assert "رمز" in r.text or "password" in r.text.lower()

    async def test_connect_trade_correct_password_not_401(self, client, test_user_and_token) -> None:
        # فقط تأیید که password check رد نمی‌شه (ممکنه mock نبودن → 400 یا 500 بده)
        mock_ex = make_mock_exchange(balances=[])
        # connect_trade_token انتظار result.to_dict() داره → MagicMock با to_dict
        fake_result = MagicMock()
        fake_result.to_dict.return_value = {"connected": True, "trade_connected": True}
        with patch(
            "app.services.wallex.service.WallexExchange.create",
            return_value=mock_ex,
        ), patch(
            "app.services.wallex.service.connect_trade_token",
            new=AsyncMock(return_value=fake_result),
        ):
            r = await client.post(
                "/v1/user/wallex/connect-trade",
                headers=auth_headers(test_user_and_token["token"]),
                json={"trade_token": "valid-trade-token-12345", "password": "TestPass123!@#"},
            )
        assert r.status_code != 401, f"Correct password should not 401: {r.text[:200]}"
