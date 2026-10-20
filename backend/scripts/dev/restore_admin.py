import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import asyncio
import uuid
import bcrypt
from sqlalchemy import select
from app.infrastructure.db.session import SessionLocal, engine
from app.infrastructure.db.models.user import User

EMAIL = "hsargoli@gmail.com"
ORIGINAL_PASSWORD = "Hossein12345" # رمزی که خودت قبلا گفتی

async def main():
    async with SessionLocal() as session:
        res = await session.execute(select(User).where(User.email == EMAIL))
        user = res.scalar_one_or_none()
        if not user:
            print("❌ کاربر پیدا نشد!")
            return
        
        pwd_hash = bcrypt.hashpw(ORIGINAL_PASSWORD.encode(), bcrypt.gensalt()).decode()
        user.password_hash = pwd_hash
        user.token_version = 1  # بازگرداندن به حالت اول
        await session.commit()
        print(f"✅ اکانت {EMAIL} بازسازی شد. رمز: {ORIGINAL_PASSWORD} | token_version: 1")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
