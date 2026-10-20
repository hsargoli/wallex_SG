import asyncio
import httpx
from httpx import ASGITransport
from app.main import app
from app.infrastructure.db.session import engine

EMAIL = "hsargoli@gmail.com"

async def main():
    print(f"⏳ ارسال درخواست فراموشی رمز برای {EMAIL} ...")
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.post("/v1/auth/forgot-password", json={"email": EMAIL})
        if r.status_code == 200:
            print("✅ ایمیل جدید با موفقیت ارسال شد.")
            print("👀 حالا برو به جیمیلت، آخرین ایمیل رو باز کن و روی لینک کلیک کن (توی مرورگر).")
        else:
            print(f"❌ خطا: {r.text}")
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
