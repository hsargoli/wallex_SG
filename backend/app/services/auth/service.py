"""Auth Service — منطق register + login.

منابع:
- docs/design/AUTH.md v1.1
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import (
    create_user_token,
    hash_password,
    verify_password,
)
from app.infrastructure.db.repositories import UserRepository
from app.services.auth.merge import cleanup_guest, merge_guest_into_user

# ═══ Config ═══
REGISTER_IP_LIMIT_HOURS = int(os.getenv("REGISTER_IP_LIMIT_HOURS", "24"))
MIN_PASSWORD_LENGTH = 8

# ═══ Simple email regex (کافی برای MVP) ═══
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


# ═══ Exceptions ═══
class AuthError(Exception):
    """خطای auth — با code و message."""

    def __init__(self, code: str, message: str, status: int = 400):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status


# ═══ Result ═══
@dataclass
class AuthResult:
    """نتیجه‌ی register/login."""

    user_token: str
    user_id: str
    email: str
    capital_total: float
    merged: bool = False
    merged_from_guest: bool = False
    merged_capital: float = 0.0
    merged_positions: int = 0

    def to_dict(self) -> dict:
        return {
            "user_token": self.user_token,
            "user_id": self.user_id,
            "email": self.email,
            "capital_total": float(self.capital_total),
            "merged": self.merged,
            "merged_from_guest": self.merged_from_guest,
            "merged_capital": float(self.merged_capital),
            "merged_positions": self.merged_positions,
        }


# ═══ Validators ═══

def _validate_email(email: str) -> str:
    if not email or not isinstance(email, str):
        raise AuthError("invalid_email", "ایمیل لازم است")
    email = email.strip().lower()
    if not _EMAIL_RE.match(email):
        raise AuthError("invalid_email", "فرمت ایمیل معتبر نیست")
    if len(email) > 255:
        raise AuthError("invalid_email", "ایمیل بیش از حد طولانی است")
    return email


def _validate_password(password: str) -> None:
    if not password or not isinstance(password, str):
        raise AuthError("invalid_password", "پسورد لازم است")
    if len(password) < MIN_PASSWORD_LENGTH:
        raise AuthError(
            "weak_password",
            f"پسورد باید حداقل {MIN_PASSWORD_LENGTH} کاراکتر باشد",
        )


# ═══ Register ═══

async def register_user(
    session: AsyncSession,
    email: str,
    password: str,
    ip: str | None = None,
    guest_token: str | None = None,
) -> AuthResult:
    """ثبت‌نام کاربر جدید.

    اگه guest_token داده شده و state مهمان موجود باشه،
    پول و positions منتقل می‌شن.

    Raises:
        AuthError: در صورت خطا (email تکراری، rate limit، پسورد ضعیف)
    """
    email = _validate_email(email)
    _validate_password(password)

    repo = UserRepository(session)

    # ─── Rate limit (۱/روز/IP) ───
    if ip:
        recent = await repo.count_recent_attempts(
            ip, hours=REGISTER_IP_LIMIT_HOURS, only_success=True
        )
        if recent >= 1:
            raise AuthError(
                "rate_limit",
                f"امکان ثبت‌نام جدید از این IP تا {REGISTER_IP_LIMIT_HOURS} ساعت آینده نیست",
                status=429,
            )

    # ─── چک email تکراری ───
    existing = await repo.get_by_email(email)
    if existing is not None:
        if ip:
            await repo.log_attempt(ip, email, success=False)
            await session.commit()
        raise AuthError(
            "email_exists",
            "این ایمیل قبلاً ثبت شده — وارد شو یا از ایمیل دیگه استفاده کن",
            status=409,
        )

    # ─── merge از guest (اختیاری) ───
    merged_data = merge_guest_into_user(guest_token)

    # ─── ساخت کاربر ───
    try:
        pwd_hash = hash_password(password)
        user = await repo.create(
            email=email,
            password_hash=pwd_hash,
            capital_total=merged_data.capital_total,
            capital_available=merged_data.capital_available,
            open_positions=merged_data.open_positions,
            closed_trades=merged_data.closed_trades,
            equity_curve=merged_data.equity_curve,
            total_trades=merged_data.total_trades,
            wins=merged_data.wins,
            losses=merged_data.losses,
        )

        if ip:
            await repo.log_attempt(ip, email, success=True)

        await session.commit()
        await session.refresh(user)

        # ─── پاک‌سازی guest (فقط بعد از commit موفق) ───
        cleanup_guest(guest_token, merged_data.merged)

        # ─── JWT ───
        token = create_user_token(str(user.id), user.email, user.token_version)

        return AuthResult(
            user_token=token,
            user_id=str(user.id),
            email=user.email,
            capital_total=float(user.capital_total),
            merged=merged_data.merged,
            merged_from_guest=merged_data.merged,
            merged_capital=merged_data.capital_total - 10_000_000.0 if merged_data.merged else 0.0,  # per Hosein 2026-10-31
            merged_positions=len(merged_data.open_positions),
        )

    except Exception as e:
        await session.rollback()
        if isinstance(e, AuthError):
            raise
        raise AuthError("server_error", f"خطای سرور: {e}", status=500) from e


# ═══ Login ═══

async def login_user(
    session: AsyncSession,
    email: str,
    password: str,
) -> AuthResult:
    """ورود کاربر.

    Raises:
        AuthError: email/پسورد اشتباه
    """
    email = _validate_email(email)
    if not password:
        raise AuthError("invalid_password", "پسورد لازم است")

    repo = UserRepository(session)

    user = await repo.get_by_email(email)
    if user is None or not user.is_active:
        # پیام یکسان با پسورد اشتباه — برای جلوگیری از user enumeration
        raise AuthError(
            "invalid_credentials",
            "ایمیل یا پسورد اشتباه است",
            status=401,
        )

    if not verify_password(password, user.password_hash):
        raise AuthError(
            "invalid_credentials",
            "ایمیل یا پسورد اشتباه است",
            status=401,
        )

    # ─── آپدیت last_seen ───
    await repo.touch_last_seen(user.id)
    await session.commit()

    # ─── JWT ───
    token = create_user_token(str(user.id), user.email, user.token_version)

    return AuthResult(
        user_token=token,
        user_id=str(user.id),
        email=user.email,
        capital_total=float(user.capital_total),
    )
