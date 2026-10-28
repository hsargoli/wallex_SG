"""Phase C2: start creates default UserBotConfig if missing (NullPool isolated)."""
import uuid
from unittest.mock import AsyncMock, patch

import httpx
import pytest
import pytest_asyncio
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.main import app
from app.infrastructure.db.base import Base
from app.infrastructure.db.session import DATABASE_URL
from app.infrastructure.db.models.user import User
from app.infrastructure.db.models.user_bot_config import UserBotConfig
from app.presentation.api.v1.auth import require_user_token
from app.services.bots import bot_registry
import app.presentation.api.v1.bots as bots_mod


@pytest_asyncio.fixture
async def test_engine():
    e = create_async_engine(DATABASE_URL, poolclass=NullPool)
    async with e.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield e
    await e.dispose()


@pytest_asyncio.fixture
async def test_session(test_engine, monkeypatch):
    sm = async_sessionmaker(test_engine, expire_on_commit=False)
    monkeypatch.setattr(bots_mod, "SessionLocal", sm)
    return sm


@pytest_asyncio.fixture
async def db_user(test_session):
    user_id = uuid.uuid4()
    async with test_session() as s:
        s.add(User(id=user_id, email=f"c2-{user_id.hex[:6]}@test.local", password_hash="x"))
        await s.commit()
    yield user_id
    async with test_session() as s:
        await s.execute(delete(UserBotConfig).where(UserBotConfig.user_id == user_id))
        await s.execute(delete(User).where(User.id == user_id))
        await s.commit()


@pytest_asyncio.fixture
async def client():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.mark.asyncio
async def test_start_creates_default_config_if_missing(db_user, test_session, client):
    bot = bot_registry.get("scalp_master")
    assert bot is not None
    app.state.exchange = object()
    app.dependency_overrides[require_user_token] = lambda: {"sub": str(db_user)}
    try:
        with patch.object(bot, "start", new=AsyncMock(return_value={"status": "started"})):
            r = await client.post("/v1/bots/scalp_master/start")
            assert r.status_code == 200, r.text
    finally:
        app.dependency_overrides.clear()

    async with test_session() as s:
        res = await s.execute(select(UserBotConfig).where(UserBotConfig.user_id == db_user))
        cfg = res.scalar_one_or_none()
        assert cfg is not None
        assert cfg.mode == "paper"
        assert float(cfg.capital_allocated) == 300000.0
