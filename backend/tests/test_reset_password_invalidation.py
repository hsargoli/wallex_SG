"""Test: reset_password must invalidate existing JWTs (token_version++).

Security: if attacker stole a JWT, after victim resets password via
forgot-password flow, the old JWT must return 401.
"""
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete

from app.core.auth import create_user_token
from app.infrastructure.db.models.user import User
from app.infrastructure.db.session import SessionLocal, engine
from app.infrastructure.db.repositories.auth_token_repo import AuthTokenRepository
from app.infrastructure.db.repositories.user_repo import UserRepository
from app.domain.entities.auth_token import AuthToken
from app.main import app
from datetime import datetime, timezone, timedelta
import uuid
import hashlib


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
async def user_with_reset_token():
    import bcrypt
    user_id = uuid.uuid4()
    email = f"reset-{user_id.hex[:8]}@example.local"
    raw_token = "test-reset-token-" + user_id.hex
    pwd_hash = bcrypt.hashpw(b"old-password", bcrypt.gensalt()).decode("utf-8")

    async with SessionLocal() as session:
        user = User(
            id=user_id,
            email=email,
            password_hash=pwd_hash,
            token_version=1,
        )
        session.add(user)
        await session.commit()

        # ساخت auth_token نوع reset_password از طریق repo (DRY)
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        repo = AuthTokenRepository(session)
        await repo.create(AuthToken(
            id=uuid.uuid4(),
            user_id=user_id,
            token_hash=token_hash,
            token_type="reset_password",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            created_at=datetime.now(timezone.utc),
        ))

    old_jwt = create_user_token(str(user_id), email, token_version=1)

    yield {
        "user_id": user_id,
        "email": email,
        "raw_token": raw_token,
        "old_jwt": old_jwt,
    }

    async with SessionLocal() as session:
        await session.execute(delete(User).where(User.id == user_id))
        await session.commit()


@pytest.mark.asyncio
async def test_reset_password_invalidates_old_jwt(client, user_with_reset_token):
    """Old JWT must be rejected after reset_password."""
    old_jwt = user_with_reset_token["old_jwt"]

    # 1. JWT قدیمی هنوز معتبره (قبل از reset)
    r = await client.get(
        "/v1/auth/me",
        headers={"Authorization": f"Bearer {old_jwt}"},
    )
    assert r.status_code == 200, f"pre-reset JWT should be valid: {r.status_code} {r.text[:200]}"

    # 2. reset password
    r = await client.post(
        "/v1/auth/reset-password",
        json={
            "token": user_with_reset_token["raw_token"],
            "new_password": "new-password-456",
        },
    )
    assert r.status_code == 200, f"reset should succeed: {r.status_code} {r.text[:200]}"

    # 3. JWT قدیمی باید 401 بده
    r = await client.get(
        "/v1/auth/me",
        headers={"Authorization": f"Bearer {old_jwt}"},
    )
    assert r.status_code == 401, (
        f"SECURITY BUG: old JWT still valid after password reset "
        f"(status={r.status_code}). token_version++ missing in reset_password."
    )
