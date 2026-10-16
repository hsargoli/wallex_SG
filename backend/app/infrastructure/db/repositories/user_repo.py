"""UserRepository — CRUD operations روی users."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.models.user import RegisterAttempt, User


class UserRepository:
    """Repository برای User + RegisterAttempt."""

    def __init__(self, session: AsyncSession):
        self.session = session

    # ═══════════════════════════════════════════
    # User CRUD
    # ═══════════════════════════════════════════

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        """یافتن کاربر با UUID."""
        result = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        """یافتن کاربر با email (case-insensitive)."""
        if not email:
            return None
        result = await self.session.execute(
            select(User).where(func.lower(User.email) == email.lower().strip())
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        email: str,
        password_hash: str,
        capital_total: float = 3_000_000.0,
    ) -> User:
        """ساخت کاربر جدید."""
        user = User(
            email=email.strip(),
            password_hash=password_hash,
            capital_total=capital_total,
            capital_available=capital_total,
            capital_in_use=0,
        )
        self.session.add(user)
        await self.session.flush()  # برای گرفتن id
        await self.session.refresh(user)  # برای server_defaultها
        return user

    async def touch_last_seen(self, user_id: uuid.UUID) -> None:
        """آپدیت last_seen_at."""
        await self.session.execute(
            update(User)
            .where(User.id == user_id)
            .values(last_seen_at=datetime.now(timezone.utc))
        )

    # ═══════════════════════════════════════════
    # Register attempts (rate limit)
    # ═══════════════════════════════════════════

    async def count_recent_attempts(
        self,
        ip: str,
        hours: int = 24,
        only_success: bool = True,
    ) -> int:
        """شمارش تلاش‌های اخیر از یه IP."""
        since = datetime.now(timezone.utc) - timedelta(hours=hours)
        query = select(func.count(RegisterAttempt.id)).where(
            RegisterAttempt.ip_address == ip,
            RegisterAttempt.attempted_at >= since,
        )
        if only_success:
            query = query.where(RegisterAttempt.success.is_(True))
        result = await self.session.execute(query)
        return result.scalar_one() or 0

    async def log_attempt(
        self,
        ip: str,
        email: str,
        success: bool,
    ) -> RegisterAttempt:
        """ثبت تلاش ثبت‌نام."""
        attempt = RegisterAttempt(
            ip_address=ip,
            email=email.strip(),
            success=success,
        )
        self.session.add(attempt)
        await self.session.flush()
        return attempt
