import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app
from app.core.rate_limit import limiter
from app.infrastructure.db.session import engine

@pytest.fixture(autouse=True)
async def dispose_engine():
    """بعد از هر تست، اتصال دیتابیس را قطع می‌کنیم تا لوپ بعدی کرش نکند."""
    yield
    await engine.dispose()

@pytest.mark.asyncio
async def test_forgot_password_rate_limit():
    """تست اعمال محدودیت ۳ درخواست در دقیقه برای فراموشی رمز."""
    limiter._storage.reset()
    
    async with app.router.lifespan_context(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            for i in range(3):
                response = await client.post("/v1/auth/forgot-password", json={"email": "test@example.com"})
                assert response.status_code != 429, f"درخواست {i+1} نباید محدود شود"
            
            response = await client.post("/v1/auth/forgot-password", json={"email": "test@example.com"})
            assert response.status_code == 429, "درخواست چهارم باید با خطای 429 رد شود"

@pytest.mark.asyncio
async def test_login_rate_limit():
    """تست اعمال محدودیت ۵ درخواست در دقیقه برای لاگین."""
    limiter._storage.reset()
    
    async with app.router.lifespan_context(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            for i in range(5):
                response = await client.post("/v1/auth/login", json={"email": "test@example.com", "password": "wrongpassword"})
                assert response.status_code != 429, f"درخواست {i+1} نباید محدود شود"
                
            response = await client.post("/v1/auth/login", json={"email": "test@example.com", "password": "wrongpassword"})
            assert response.status_code == 429, "درخواست ششم باید با خطای 429 رد شود"
