import asyncio
from datetime import datetime, timezone
from sqlalchemy import select
from app.infrastructure.db.session import SessionLocal, engine
from app.infrastructure.db.models.auth_token import AuthTokenModel

async def main():
    async with SessionLocal() as session:
        result = await session.execute(select(AuthTokenModel).order_by(AuthTokenModel.created_at.desc()))
        token = result.scalars().first()
        if token:
            print(f"  Created: {token.created_at} (tzinfo: {token.created_at.tzinfo})")
            print(f"  Expires: {token.expires_at} (tzinfo: {token.expires_at.tzinfo})")
            now = datetime.now(timezone.utc)
            print(f"  Now UTC: {now}")
            
            # منطق فعلی کد
            is_expired = token.expires_at.replace(tzinfo=timezone.utc) < now
            print(f"  Is expired (طبق کد فعلی): {is_expired}")
        else:
            print("  ❌ هیچ توکنی در دیتابیس نیست!")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
