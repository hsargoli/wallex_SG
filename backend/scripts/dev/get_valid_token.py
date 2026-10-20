import asyncio
import secrets
import hashlib
from sqlalchemy import select
from app.infrastructure.db.session import SessionLocal, engine
from app.infrastructure.db.models.user import User
from app.infrastructure.db.models.auth_token import AuthTokenModel
from datetime import datetime, timezone, timedelta

async def main():
    async with SessionLocal() as session:
        res = await session.execute(select(User).where(User.email == "hsargoli@gmail.com"))
        user = res.scalar_one_or_none()
        
        # ساخت یک توکن جدید مستقیم در دیتابیس برای تست
        raw_token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        
        at = AuthTokenModel(
            id=uuid.uuid4(),
            user_id=user.id,
            token_hash=token_hash,
            token_type="reset_password",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            created_at=datetime.now(timezone.utc)
        )
        session.add(at)
        await session.commit()
        print(raw_token)
    await engine.dispose()

import uuid
if __name__ == "__main__":
    asyncio.run(main())
