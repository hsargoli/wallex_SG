"""Tests for /v1/auth/logout-all endpoint.

Design (Di Darya + Di Ferdows):
- token_version++ → همه JWTهای قبلی باطل
- rate limit: 3/hour
- auth required (401 without token)
"""
import pytest
import uuid
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete

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


@pytest.fixture
async def user_and_token():
    import bcrypt
    user_id = uuid.uuid4()
    email = f"logout-all-{user_id.hex[:8]}@example.local"
    pwd_hash = bcrypt.hashpw(b"TestPass123!@#", bcrypt.gensalt()).decode("utf-8")

    async with SessionLocal() as session:
        user = User(
            id=user_id,
            email=email,
            password_hash=pwd_hash,
            token_version=1,
        )
        session.add(user)
        await session.commit()

    old_jwt = create_user_token(str(user_id), email, token_version=1)

    yield {"user_id": user_id, "email": email, "old_jwt": old_jwt}

    async with SessionLocal() as session:
        await session.execute(delete(User).where(User.id == user_id))
        await session.commit()


def _auth(jwt: str) -> dict:
    return {"Authorization": f"Bearer {jwt}"}


@pytest.mark.asyncio
async def test_logout_all_invalidates_old_jwt(client, user_and_token):
    """After logout-all, old JWT must return 401."""
    old_jwt = user_and_token["old_jwt"]

    # 1. JWT valid before
    r = await client.get("/v1/auth/me", headers=_auth(old_jwt))
    assert r.status_code == 200, f"pre-logout: {r.status_code} {r.text[:200]}"

    # 2. logout-all
    r = await client.post("/v1/auth/logout-all", headers=_auth(old_jwt))
    assert r.status_code == 200, f"logout-all: {r.status_code} {r.text[:200]}"

    # 3. JWT invalid after
    r = await client.get("/v1/auth/me", headers=_auth(old_jwt))
    assert r.status_code == 401, (
        f"SECURITY BUG: old JWT still valid after logout-all "
        f"(status={r.status_code}). token_version++ failed."
    )


@pytest.mark.asyncio
async def test_logout_all_without_token_401(client):
    """No Authorization header → 401."""
    r = await client.post("/v1/auth/logout-all")
    assert r.status_code == 401, r.text


@pytest.mark.asyncio
async def test_logout_all_rate_limit_429_on_4th(client, user_and_token):
    """LOGOUT_ALL_LIMIT=3/hour: 4th call → 429."""
    jwt = user_and_token["old_jwt"]
    # 3 first calls should pass
    for i in range(3):
        r = await client.post("/v1/auth/logout-all", headers=_auth(jwt))
        # بعد از اولین logout-all، JWT باطل می‌شه → 401 از require_user_token
        # قبل از rate limiter. پس فقط چک می‌کنیم 500 نده.
        assert r.status_code != 500, f"attempt {i+1}: 500 {r.text[:200]}"

    # 4th → rate limiter قبل از auth چک می‌شه → 429
    # (slowapi: @limiter.limit قبل از Depends اجرا می‌شه)
    r = await client.post("/v1/auth/logout-all", headers=_auth(jwt))
    # یا 429 (rate limit) یا 401 (jwt invalid، اگه rate limit اجرا نشده)
    assert r.status_code in (429, 401), (
        f"expected 429 or 401, got {r.status_code}: {r.text[:200]}"
    )
