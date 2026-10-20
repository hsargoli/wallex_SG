"""Fix #3 — rate limit tests for security-critical endpoints.

ADR 0028: every endpoint with @limiter.limit MUST have `response: Response`.
Prime rule 12: test fail = gift.
"""
import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture(autouse=True)
async def _cleanup():
    """Reset limiter + dispose DB engine per test.

    Why dispose: test_register opens DB connections. Without dispose,
    the old asyncpg connection is orphaned on the closed event loop
    when the next test starts -> "Event loop is closed" on teardown.
    """
    from app.core.rate_limit import limiter
    storage = getattr(limiter, "_storage", None)
    if storage is not None and hasattr(storage, "storage"):
        try:
            storage.storage.clear()
        except Exception:
            pass

    yield

    try:
        from app.infrastructure.db.session import engine
        await engine.dispose()
    except Exception:
        pass


@pytest.fixture
async def client():
    # No lifespan_context: auth endpoints don't need background tasks
    # (ticker_ws, guest scheduler). Lifespan leaves DB connections open
    # after pytest closes the event loop -> "Event loop is closed" in teardown.
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.mark.asyncio
async def test_register_rate_limit_429_on_4th(client):
    """REGISTER_LIMIT=3/hour: 4th → 429. Also: no 500 (ADR 0028 sanity)."""
    payload = {"email": "rl_test_fix3_1@example.com", "password": "Abc12345!@#"}
    for i in range(3):
        r = await client.post("/v1/auth/register", json=payload)
        assert r.status_code != 500, f"attempt {i+1} 500: {r.text[:300]}"
    r = await client.post("/v1/auth/register", json=payload)
    assert r.status_code == 429, f"expected 429, got {r.status_code}: {r.text[:200]}"


@pytest.mark.asyncio
async def test_reset_password_rate_limit_429_on_6th(client):
    """RESET_PASSWORD_LIMIT=5/hour: 6th → 429."""
    payload = {
        "token": "eyJhbGciOiJIUzI1NiJ9.eyJmYWtlIjoxfQ.fake_sig_long_enough_for_test",
        "new_password": "Abc12345!@#",
    }
    for i in range(5):
        r = await client.post("/v1/auth/reset-password", json=payload)
        assert r.status_code != 500, f"attempt {i+1} 500: {r.text[:300]}"
    r = await client.post("/v1/auth/reset-password", json=payload)
    assert r.status_code == 429, f"expected 429, got {r.status_code}: {r.text[:200]}"
