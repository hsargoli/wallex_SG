import asyncio
import httpx
import secrets
import hashlib
from httpx import ASGITransport
from sqlalchemy import select

from app.main import app
from app.infrastructure.db.session import SessionLocal, engine
from app.infrastructure.db.models.user import User
from app.infrastructure.db.models.auth_token import AuthTokenModel

EMAIL = "hsargoli@gmail.com"
NEW_PASS = "NewSecurePass456!@#"

async def main():
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        print(f"🔹 [1/3] درخواست forgot-password برای {EMAIL} ...")
        r = await client.post("/v1/auth/forgot-password", json={"email": EMAIL})
        print(f"   Status: {r.status_code}")

        print("🔹 [2/3] استخراج توکن از دیتابیس و شبیه‌سازی کلیک کاربر ...")
        async with SessionLocal() as session:
            res = await session.execute(select(User).where(User.email == EMAIL))
            user = res.scalar_one_or_none()
            if not user:
                print("❌ کاربر پیدا نشد")
                return

            res = await session.execute(select(AuthTokenModel).where(AuthTokenModel.user_id == user.id, AuthTokenModel.token_type == "reset_password"))
            token_rec = res.scalars().first()
            if not token_rec:
                print("❌ توکنی در دیتابیس نیست")
                return
            
            # توکن خام رو می‌سازیم و هشش رو جایگزین می‌کنیم
            raw_token = secrets.token_urlsafe(32)
            token_rec.token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
            await session.commit()
            print(f"   ✅ توکن آماده شد: {raw_token[:10]}...")

        print("🔹 [3/3] فراخوانی /reset-password (مستقیم به بک‌اند) ...")
        r = await client.post("/v1/auth/reset-password", json={"token": raw_token, "new_password": NEW_PASS})
        print(f"\n🔴 وضعیت پاسخ: {r.status_code}")
        print(f"🔴 بدنه پاسخ: {r.text}")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
