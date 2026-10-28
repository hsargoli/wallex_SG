"""UserBotConfig — per-user, per-bot configuration + safety layers."""
from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.base import Base


class UserBotConfig(Base):
    """Config هر کاربر برای هر ربات (paper/live + امنیت)."""

    __tablename__ = "user_bot_configs"
    __table_args__ = (
        UniqueConstraint("user_id", "bot_slug", name="uix_user_bot"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    bot_slug: Mapped[str] = mapped_column(String(50), nullable=False)

    # mode
    mode: Mapped[str] = mapped_column(
        String(20), default="paper", server_default=text("'paper'"), nullable=False
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default=text("false"), nullable=False
    )

    # capital
    capital_allocated: Mapped[Decimal] = mapped_column(
        Numeric(20, 2), default=Decimal("0.00"), server_default=text("0.00"), nullable=False
    )

    # D+ safety layers
    live_stage: Mapped[int] = mapped_column(
        Integer, default=0, server_default=text("0"), nullable=False
    )  # 0=paper, 1=test, 2=live-active
    daily_loss_limit_pct: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), default=Decimal("3.00"), server_default=text("3.00"), nullable=False
    )
    kill_switch_auto: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default=text("false"), nullable=False
    )
    kill_switch_manual: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default=text("false"), nullable=False
    )

    # timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
