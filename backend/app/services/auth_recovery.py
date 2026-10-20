"""Auth Recovery Services — Forgot Password & Email Verification."""
import hashlib
import secrets
import uuid
from datetime import datetime, timezone, timedelta
import structlog

from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.db.repositories.user_repo import UserRepository
from app.infrastructure.db.repositories.auth_token_repo import AuthTokenRepository
from app.infrastructure.email.mock_sender import MockEmailSender
from app.domain.entities.auth_token import AuthToken
from app.core.config import get_settings

log = structlog.get_logger("auth.recovery")

def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()

async def request_password_reset(session: AsyncSession, email: str) -> None:
    """درخواست فراموشی رمز: ساخت توکن و ارسال ایمیل."""
    user_repo = UserRepository(session)
    token_repo = AuthTokenRepository(session)
    user = await user_repo.get_by_email(email)
    
    # برای جلوگیری از افشای وجود ایمیل، همیشه موفقیت برمی‌گردانیم
    if not user:
        log.info("password_reset_ignored_unknown_email", email=email)
        return

    # حذف توکن‌های قبلی از یک نوع
    await token_repo.delete_by_user_and_type(user.id, "reset_password")

    raw_token = secrets.token_urlsafe(32)
    token_hash = _hash_token(raw_token)
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)

    auth_token = AuthToken(
        id=uuid.uuid4(),
        user_id=user.id,
        token_hash=token_hash,
        token_type="reset_password",
        expires_at=expires_at,
        created_at=datetime.now(timezone.utc)
    )
    await token_repo.create(auth_token)

    settings = get_settings()
    reset_link = f"{settings.FRONTEND_URL}/reset-password?token={raw_token}"
    
    email_sender = MockEmailSender() # بعداً بر اساس ENV به Resend سوییچ می‌شود
    await email_sender.send(
        to=user.email,
        subject="بازیابی رمز عبور | SarvBots",
        body=f"برای تغییر رمز عبور روی لینک زیر کلیک کنید:\n{reset_link}"
    )
    log.info("password_reset_sent", user_id=str(user.id)[:8])

async def reset_password(session: AsyncSession, raw_token: str, new_password: str) -> bool:
    """تغییر رمز عبور با استفاده از توکن."""
    token_repo = AuthTokenRepository(session)
    user_repo = UserRepository(session)
    
    token_hash = _hash_token(raw_token)
    auth_token = await token_repo.get_by_hash(token_hash)

    if not auth_token or auth_token.token_type != "reset_password":
        return False
    
    if auth_token.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        await token_repo.delete_by_user_and_type(auth_token.user_id, "reset_password")
        return False

    # تغییر رمز
    user = await user_repo.get_by_id(auth_token.user_id)
    if not user:
        return False
        
    import bcrypt
    new_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    user.password_hash = new_hash
    user.token_version = user.token_version + 1  # invalidate all existing JWTs
    await session.commit()

    # پاک کردن توکن
    await token_repo.delete_by_user_and_type(user.id, "reset_password")
    log.info("password_reset_success", user_id=str(user.id)[:8])
    return True

async def request_email_verification(session: AsyncSession, email: str) -> None:
    """درخواست تایید ایمیل."""
    user_repo = UserRepository(session)
    token_repo = AuthTokenRepository(session)
    user = await user_repo.get_by_email(email)
    
    if not user or user.is_verified:
        return

    await token_repo.delete_by_user_and_type(user.id, "verify_email")

    raw_token = secrets.token_urlsafe(32)
    token_hash = _hash_token(raw_token)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=24)

    auth_token = AuthToken(
        id=uuid.uuid4(),
        user_id=user.id,
        token_hash=token_hash,
        token_type="verify_email",
        expires_at=expires_at,
        created_at=datetime.now(timezone.utc)
    )
    await token_repo.create(auth_token)

    settings = get_settings()
    verify_link = f"{settings.FRONTEND_URL}/verify-email?token={raw_token}"
    
    email_sender = MockEmailSender()
    await email_sender.send(
        to=user.email,
        subject="تایید ایمیل | SarvBots",
        body=f"برای تایید ایمیل خود روی لینک زیر کلیک کنید:\n{verify_link}"
    )
    log.info("email_verification_sent", user_id=str(user.id)[:8])

async def verify_email(session: AsyncSession, raw_token: str) -> bool:
    """تایید ایمیل با استفاده از توکن."""
    token_repo = AuthTokenRepository(session)
    user_repo = UserRepository(session)
    
    token_hash = _hash_token(raw_token)
    auth_token = await token_repo.get_by_hash(token_hash)

    if not auth_token or auth_token.token_type != "verify_email":
        return False
    
    if auth_token.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        return False

    user = await user_repo.get_by_id(auth_token.user_id)
    if not user:
        return False

    user.is_verified = True
    await session.commit()

    await token_repo.delete_by_user_and_type(user.id, "verify_email")
    log.info("email_verification_success", user_id=str(user.id)[:8])
    return True
