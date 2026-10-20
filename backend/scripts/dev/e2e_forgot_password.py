import asyncio
import uuid
import bcrypt
import httpx
from httpx import ASGITransport
from sqlalchemy import select

from app.main import app
from app.infrastructure.db.session import SessionLocal, engine
from app.infrastructure.db.models.user import User
from app.infrastructure.db.models.auth_token import AuthTokenModel

EMAIL = "hsargoli@gmail.com"
OLD_PASSWORD = "TestPass123!@#"
NEW_PASSWORD = "NewSecurePass456!@#"

async def main():
    print(f"🔹 [1/5] آماده‌سازی کاربر در دیتابیس: {EMAIL}")
    async with SessionLocal() as session:
        res = await session.execute(select(User).where(User.email == EMAIL))
        user = res.scalar_one_or_none()
        pwd_hash = bcrypt.hashpw(OLD_PASSWORD.encode(), bcrypt.gensalt()).decode()
        
        if not user:
            user = User(id=uuid.uuid4(), email=EMAIL, password_hash=pwd_hash, token_version=1, is_verified=False)
            session.add(user)
        else:
            user.password_hash = pwd_hash
        await session.commit()
        user_id = user.id

    print("\n🔹 [2/5] درخواست 'فراموشی رمز' (ارسال ایمیل واقعی)...")
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.post("/v1/auth/forgot-password", json={"email": EMAIL})
        if r.status_code != 200:
            print(f"❌ خطا در درخواست فراموشی رمز: {r.text}")
            return
        print(f"✅ پاسخ API: {r.json()}")
        print(f"📧 یک ایمیل حاوی لینک بازیابی به {EMAIL} ارسال شد. (جیمیل را چک کنید)")

    print("\n🔹 [3/5] استخراج توکن بازیابی از دیتابیس (شبیه‌سازی کلیک روی لینک ایمیل)...")
    await asyncio.sleep(2)  # صبر برای ثبت در دیتابیس
    async with SessionLocal() as session:
        res = await session.execute(
            select(AuthTokenModel)
            .where(AuthTokenModel.user_id == user_id, AuthTokenModel.token_type == "reset_password")
            .order_by(AuthTokenModel.created_at.desc())
        )
        token_rec = res.scalars().first()
        if not token_rec:
            print("❌ توکنی در دیتابیس پیدا نشد!")
            return
        # چون ما توکن هش شده رو ذخیره می‌کنیم، برای تست باید یک توکن معتبر بسازیم
        # (در دنیای واقعی کاربر روی لینک کلیک می‌کند که حاوی توکن خام است)
        # اینجا ما نمیتونیم توکن خام رو از هش دربیاریم، پس یک توکن تستی میسازیم
        # و اون رو در دیتابیس به روز میکنیم تا با هم مچ بشن.
        import secrets, hashlib
        raw_token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        token_rec.token_hash = token_hash
        await session.commit()
        print(f"✅ توکن بازیابی آماده شد: {raw_token[:15]}...")

    print("\n🔹 [4/5] ارسال رمز جدید با توکن (تغییر رمز)...")
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.post(
            "/v1/auth/reset-password",
            json={"token": raw_token, "new_password": NEW_PASSWORD}
        )
        if r.status_code != 200:
            print(f"❌ خطا در تغییر رمز: {r.text}")
            return
        print(f"✅ پاسخ API: {r.json()}")

    print("\n🔹 [5/5] تست لاگین با رمز جدید...")
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.post("/v1/auth/login", json={"email": EMAIL, "password": NEW_PASSWORD})
        if r.status_code == 200:
            print("🎉 عالی! لاگین با رمز جدید با موفقیت انجام شد.")
            print("👀 حالا برو ایمیل hsargoli@gmail.com را چک کن. باید ایمیل بازیابی رمز رو دریافت کرده باشی.")
        else:
            print(f"❌ لاگین با رمز جدید شکست خورد: {r.text}")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
