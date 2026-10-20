"""Test: /connect and /connect-trade return soft-warning for unverified users."""
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete
from unittest.mock import patch, MagicMock, AsyncMock
import uuid
import bcrypt

from app.core.auth import create_user_token
from app.infrastructure.db.models.user import User
from app.infrastructure.db.session import SessionLocal, engine
from app.main import app


@pytest.fixture(autouse=True)
async def _cleanup():
    from app.core.rate_limit import limiter
    storage = getattr(limiter, "_storage", None)
    if storage is not None and hasattr(storage, "storage"):
        try:
            storage.storage.clear()
        except Exception:
            pass
    yield
    try:
        await engine.dispose()
    except Exception:
        pass


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


async def _create_user(is_verified: bool):
    user_id = uuid.uuid4()
    email = f"v-{user_id.hex[:8]}@example.local"
    pwd_hash = bcrypt.hashpw(b"TestPass123!@#", bcrypt.gensalt()).decode("utf-8")

    async with SessionLocal() as session:
        user = User(
            id=user_id, email=email, password_hash=pwd_hash, token_version=1, is_verified=is_verified
        )
        session.add(user)
        await session.commit()

    jwt = create_user_token(str(user_id), email, token_version=1)
    return {"user_id": user_id, "email": email, "jwt": jwt}


@pytest.mark.asyncio
async def test_connect_unverified_has_warning(client):
    u = await _create_user(is_verified=False)
    headers = {"Authorization": f"Bearer {u['jwt']}"}
    
    mock_result = MagicMock()
    mock_result.to_dict.return_value = {"status": "connected"}

    # Patch the imported function in the endpoint's module directly
    with patch("app.presentation.api.v1.wallex.connect_token", new=AsyncMock(return_value=mock_result)):
        r = await client.post(
            "/v1/user/wallex/connect",
            headers=headers,
            json={"token": "valid-token-12345", "password": "TestPass123!@#"},
        )
    
    assert r.status_code == 200, r.text
    assert r.json().get("warning") == "email_not_verified"
    assert "warning_fa" in r.json()

    async with SessionLocal() as session:
        await session.execute(delete(User).where(User.id == u["user_id"]))
        await session.commit()


@pytest.mark.asyncio
async def test_connect_verified_no_warning(client):
    u = await _create_user(is_verified=True)
    headers = {"Authorization": f"Bearer {u['jwt']}"}
    
    mock_result = MagicMock()
    mock_result.to_dict.return_value = {"status": "connected"}

    with patch("app.presentation.api.v1.wallex.connect_token", new=AsyncMock(return_value=mock_result)):
        r = await client.post(
            "/v1/user/wallex/connect",
            headers=headers,
            json={"token": "valid-token-12345", "password": "TestPass123!@#"},
        )
    
    assert r.status_code == 200, r.text
    assert "warning" not in r.json()

    async with SessionLocal() as session:
        await session.execute(delete(User).where(User.id == u["user_id"]))
        await session.commit()
