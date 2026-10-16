"""User + RegisterAttempt models."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    Index,
    Integer,
    LargeBinary,
    Numeric,
    String,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import INET, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.base import Base


class User(Base):
    """کاربر ثبت‌نام‌شده."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    # پول مجازی
    capital_total: Mapped[float] = mapped_column(
        Numeric(20, 2), default=3_000_000, server_default=text("3000000.00")
    )
    capital_available: Mapped[float] = mapped_column(
        Numeric(20, 2), default=3_000_000, server_default=text("3000000.00")
    )
    capital_in_use: Mapped[float] = mapped_column(
        Numeric(20, 2), default=0, server_default=text("0.00")
    )

    # state
    open_positions: Mapped[list] = mapped_column(
        JSONB, default=list, server_default=text("'[]'::jsonb")
    )
    closed_trades: Mapped[list] = mapped_column(
        JSONB, default=list, server_default=text("'[]'::jsonb")
    )
    equity_curve: Mapped[list] = mapped_column(
        JSONB, default=list, server_default=text("'[]'::jsonb")
    )

    # فاز ۱۷.۷.۲ — ۱۰ فیلد بی‌خونه‌ی PaperState (ADR 0015 + Addendum 1)
    # منبع کامل: is_running, initial_capital, equity, peaks, dd, pnl,
    # win_rate, started_at, last_check_at, check_count, events, radar
    # ⚠️ ستون‌های بالا (capital_available, open_positions, ...) view آماری‌ان
    #    — فقط از طریق repo.save() هم‌زمان آپدیت می‌شن
    paper_meta: Mapped[dict] = mapped_column(
        JSONB, default=dict, server_default=text("'{}'::jsonb")
    )

    # آمار
    total_trades: Mapped[int] = mapped_column(Integer, default=0, server_default=text("0"))
    wins: Mapped[int] = mapped_column(Integer, default=0, server_default=text("0"))
    losses: Mapped[int] = mapped_column(Integer, default=0, server_default=text("0"))

    # والکس (فاز ۱۷.۸)
    wallex_token_encrypted: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    wallex_connected_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # متادیتا
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default=text("true")
    )

    __table_args__ = (
        # unique روی lower(email) — جلوگیری از User@x.com + user@x.com
        Index("uq_users_email_lower", func.lower(email), unique=True),
        Index("idx_users_created", created_at.desc()),
        CheckConstraint("capital_total >= 0", name="ck_users_capital_total_pos"),
        CheckConstraint("capital_available >= 0", name="ck_users_capital_available_pos"),
    )

    def __repr__(self) -> str:
        return f"<User {self.email}>"


class RegisterAttempt(Base):
    """تلاش‌های ثبت‌نام — برای rate limit ۱/روز/IP."""

    __tablename__ = "register_attempts"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ip_address: Mapped[str] = mapped_column(INET, nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    success: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text("false"))
    attempted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        Index("idx_register_attempts_ip_time", "ip_address", attempted_at.desc()),
    )

    def __repr__(self) -> str:
        return f"<RegisterAttempt {self.ip_address} {self.email}>"
