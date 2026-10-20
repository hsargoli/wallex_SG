"""Test: change-password must have rate limit (CHANGE_PASSWORD_LIMIT=5/hour)."""
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
    email = f"cp-{user_id.hex[:8]}@example.local"
    pwd_hash = bcrypt.hashpw(b"OldPass123!@#", bcrypt.gensalt()).decode("utf-8")

    async with SessionLocal() as session:
        user = User(id=user_id, email=email, password_hash=pwd_hash, token_version=1)
        session.add(user)
        await session.commit()

    jwt = create_user_token(str(user_id), email, token_version=1)
    yield {"user_id": user_id, "jwt": jwt}

    async with SessionLocal() as session:
        await session.execute(delete(User).where(User.id == user_id))
        await session.commit()


@pytest.mark.asyncio
async def test_change_password_rate_limit_429_on_6th(client, user_and_token):
    """CHANGE_PASSWORD_LIMIT=5/hour: 6th → 429. No 500 sanity."""
    jwt = user_and_token["jwt"]
    headers = {"Authorization": f"Bearer {jwt}"}

    # payload با رمز قدیمی اشتباه — response سریع (400)، نه 500
    payload = {"old_password": "WrongOld123!", "new_password": "NewPass123!@#"}

    for i in range(5):
        r = await client.post("/v1/auth/change-password", headers=headers, json=payload)
        assert r.status_code != 500, f"attempt {i+1}: 500 {r.text[:200]}"

    r = await client.post("/v1/auth/change-password", headers=headers, json=payload)
    assert r.status_code == 429, f"expected 429, got {r.status_code}: {r.text[:200]}"
