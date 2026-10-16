"""تست endpointهای /v1/user/paper-v3/*.

پوشش: auth (JWT)، status/reset بدون engine، start با engine واقعی، persistence.

⚠️ چرا AsyncClient و نه TestClient:
   TestClient یه portal loop جدا در thread جدا می‌سازه. engine
   (module-level) اگه توی loop pytest استفاده شده باشه، pool
   به اون loop چسبیده و endpoint توی loop TestClient
   "Future attached to different loop" می‌ده.
   راه‌حل: httpx.AsyncClient با ASGITransport — همه در یک loop.
"""

from __future__ import annotations

import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete

from app.core.auth import create_user_token
from app.infrastructure.db.models.user import User
from app.infrastructure.db.session import SessionLocal, engine
from app.main import app


@pytest.fixture(autouse=True)
async def _dispose_engine_after_test():
    """engine.dispose() بعد از هر تست — pool تازه."""
    yield
    await engine.dispose()


@pytest.fixture
async def client():
    """httpx AsyncClient با lifespan context — همه در یک loop."""
    async with app.router.lifespan_context(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            yield c


@pytest.fixture
async def test_user_and_token():
    """user جدید + JWT معتبر."""
    user_id = uuid.uuid4()
    email = f"test-api-{user_id.hex[:8]}@example.local"

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

    app.state.user_engines.pop(user_id, None)
    async with SessionLocal() as session:
        await session.execute(delete(User).where(User.id == user_id))
        await session.commit()


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


class TestAuth:
    async def test_status_without_token(self, client) -> None:
        """بدون توکن → 401."""
        r = await client.get("/v1/user/paper-v3/status")
        assert r.status_code == 401
        assert r.json()["detail"]["code"] == "missing_token"

    async def test_status_with_invalid_token(self, client) -> None:
        """توکن نامعتبر → 401."""
        r = await client.get(
            "/v1/user/paper-v3/status",
            headers={"Authorization": "Bearer invalid.token.here"},
        )
        assert r.status_code == 401

    async def test_status_with_valid_token(
        self, client, test_user_and_token
    ) -> None:
        """توکن معتبر → 200."""
        r = await client.get(
            "/v1/user/paper-v3/status",
            headers=auth_headers(test_user_and_token["token"]),
        )
        assert r.status_code == 200


class TestStatusFallback:
    async def test_status_no_engine_returns_defaults(
        self, client, test_user_and_token
    ) -> None:
        """بدون engine → state از DB (defaults)."""
        r = await client.get(
            "/v1/user/paper-v3/status",
            headers=auth_headers(test_user_and_token["token"]),
        )
        assert r.status_code == 200
        data = r.json()
        assert data["initial_capital"] == 3_000_000.0
        assert data["is_running"] is False
        assert data["open_positions"] == []


class TestStartStop:
    async def test_start_creates_engine(
        self, client, test_user_and_token
    ) -> None:
        """start → engine ساخته می‌شه."""
        token = test_user_and_token["token"]
        user_id = test_user_and_token["user_id"]

        r = await client.post(
            "/v1/user/paper-v3/start",
            headers=auth_headers(token),
            json={
                "bot_slug": "scalp_master",
                "symbols": ["BTCTMN"],
                "timeframe": "1h",
                "initial_capital": 3_000_000.0,
                "check_interval_sec": 9999,
                "position_size_pct": 50.0,
            },
        )
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["status"] in ("started", "already_running")
        assert user_id in app.state.user_engines
        assert app.state.user_engines[user_id].state.is_running is True

        r2 = await client.get(
            "/v1/user/paper-v3/status",
            headers=auth_headers(token),
        )
        assert r2.status_code == 200
        assert r2.json()["is_running"] is True

    async def test_stop_after_start(
        self, client, test_user_and_token
    ) -> None:
        """start → stop → is_running = False."""
        token = test_user_and_token["token"]

        await client.post(
            "/v1/user/paper-v3/start",
            headers=auth_headers(token),
            json={"symbols": ["BTCTMN"], "check_interval_sec": 9999},
        )

        r = await client.post(
            "/v1/user/paper-v3/stop",
            headers=auth_headers(token),
        )
        assert r.status_code == 200
        assert r.json()["status"] == "stopped"

        r2 = await client.get(
            "/v1/user/paper-v3/status",
            headers=auth_headers(token),
        )
        assert r2.json()["is_running"] is False

    async def test_stop_without_engine(
        self, client, test_user_and_token
    ) -> None:
        """stop بدون engine → noop."""
        r = await client.post(
            "/v1/user/paper-v3/stop",
            headers=auth_headers(test_user_and_token["token"]),
        )
        assert r.status_code == 200
        assert r.json()["status"] == "stopped"


class TestReset:
    async def test_reset_without_engine(
        self, client, test_user_and_token
    ) -> None:
        """reset بدون engine → state صفر."""
        token = test_user_and_token["token"]
        r = await client.post(
            "/v1/user/paper-v3/reset",
            headers=auth_headers(token),
        )
        assert r.status_code == 200, r.text
        assert r.json()["status"] == "reset"

        r2 = await client.get(
            "/v1/user/paper-v3/status",
            headers=auth_headers(token),
        )
        assert r2.json()["total_trades"] == 0

    async def test_reset_with_engine(
        self, client, test_user_and_token
    ) -> None:
        """reset با engine → از طریق engine."""
        token = test_user_and_token["token"]
        await client.post(
            "/v1/user/paper-v3/start",
            headers=auth_headers(token),
            json={"symbols": ["BTCTMN"], "check_interval_sec": 9999},
        )

        r = await client.post(
            "/v1/user/paper-v3/reset",
            headers=auth_headers(token),
        )
        assert r.status_code == 200, r.text
        assert r.json()["status"] == "reset"
