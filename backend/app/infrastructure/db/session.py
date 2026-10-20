"""Async Engine + Session برای PostgreSQL."""

from __future__ import annotations

import os
from collections.abc import AsyncIterator

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

load_dotenv()

import sys

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL تنظیم نشده — .env رو چک کن")

# محافظت از دیتابیس اصلی در زمان اجرای تست‌ها
if "pytest" in sys.modules:
    # جایگزینی نام دیتابیس با دیتابیس تست
    if "/wallex_db" in DATABASE_URL:
        DATABASE_URL = DATABASE_URL.replace("/wallex_db", "/wallex_test_db")
    elif "wallex_db" in DATABASE_URL:
        DATABASE_URL = DATABASE_URL.replace("wallex_db", "wallex_test_db")
    print("🧪 [TEST MODE] Connected to wallex_test_db")

# Engine — pool settings مناسب برای FastAPI async
engine: AsyncEngine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,  # برای connectionهای قدیمی
)

# Session factory
SessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_session() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency — AsyncSession per request."""
    async with SessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
