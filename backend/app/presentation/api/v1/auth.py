"""Auth endpoints — register + login + me.

منابع:
- docs/design/AUTH.md v1.1
"""

from __future__ import annotations

from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, Header, HTTPException, Request, status, Response
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import decode_user_token
from app.core.rate_limit import limiter, LOGIN_LIMIT, FORGOT_PASSWORD_LIMIT
from app.services.auth_recovery import request_password_reset, reset_password, request_email_verification, verify_email
from app.infrastructure.db.session import get_session
from app.services.auth import AuthError, login_user, register_user

log = structlog.get_logger("auth.api")
router = APIRouter(prefix="/auth", tags=["Auth"])


# ═══════════════════════════════════════════
# Schemas
# ═══════════════════════════════════════════

class RegisterRequest(BaseModel):
    email: str = Field(..., min_length=3, max_length=255)
    password: str = Field(..., min_length=8, max_length=128)
    guest_token: str | None = Field(default=None)


class LoginRequest(BaseModel):
    email: str = Field(..., min_length=3, max_length=255)
    password: str = Field(..., min_length=1, max_length=128)



class ForgotPasswordRequest(BaseModel):
    email: str = Field(..., min_length=3, max_length=255)

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8, max_length=128)

class VerifyEmailRequest(BaseModel):
    token: str

class AuthResponse(BaseModel):
    user_token: str
    user_id: str
    email: str
    capital_total: float
    merged: bool = False
    merged_from_guest: bool = False


class MeResponse(BaseModel):
    user_id: str
    email: str
    capital_total: float
    capital_available: float
    capital_in_use: float
    total_trades: int
    wins: int
    losses: int


# ═══════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════

def _get_client_ip(request: Request) -> str | None:
    """گرفتن IP کاربر (با احتساب proxy)."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()
    return request.client.host if request.client else None


def _auth_error_to_http(e: AuthError) -> HTTPException:
    """تبدیل AuthError به HTTPException."""
    return HTTPException(
        status_code=e.status,
        detail={"code": e.code, "message": e.message},
    )


# ═══════════════════════════════════════════
# Dependency: کاربر لاگین‌شده
# ═══════════════════════════════════════════

async def require_user_token(
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
) -> dict:
    """گرفتن و اعتبارسنجی JWT از header Authorization.

    فرمت: `Authorization: Bearer eyJ...`
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "missing_token", "message": "هدر Authorization لازم است"},
        )

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "invalid_token_format", "message": "فرمت: Bearer <token>"},
        )

    try:
        payload = decode_user_token(parts[1])
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "invalid_token", "message": f"توکن نامعتبر: {e}"},
        ) from e

    return payload


# ═══════════════════════════════════════════
# Endpoints
# ═══════════════════════════════════════════

@router.post("/register", response_model=AuthResponse, status_code=201)
async def register(
    request: Request,
    payload: RegisterRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> AuthResponse:
    """ثبت‌نام کاربر جدید."""
    ip = _get_client_ip(request)

    try:
        result = await register_user(
            session=session,
            email=payload.email,
            password=payload.password,
            ip=ip,
        )
    except AuthError as e:
        log.info("auth.register_failed", email=payload.email, code=e.code, ip=ip)
        raise _auth_error_to_http(e) from e

    log.info("auth.registered", email=result.email, user_id=result.user_id[:8], ip=ip)
    return AuthResponse(**result.to_dict())


@router.post("/login", response_model=AuthResponse)
@limiter.limit(LOGIN_LIMIT)
async def login(
    request: Request,
    response: Response,
    payload: LoginRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> AuthResponse:
    """ورود کاربر."""
    try:
        result = await login_user(
            session=session,
            email=payload.email,
            password=payload.password,
        )
    except AuthError as e:
        log.info("auth.login_failed", email=payload.email, code=e.code)
        raise _auth_error_to_http(e) from e

    log.info("auth.logged_in", email=result.email, user_id=result.user_id[:8])
    return AuthResponse(**result.to_dict())


@router.get("/me", response_model=MeResponse)
async def me(
    user: Annotated[dict, Depends(require_user_token)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> MeResponse:
    """اطلاعات کاربر لاگین‌شده."""
    from app.infrastructure.db.repositories import UserRepository

    repo = UserRepository(session)
    db_user = await repo.get_by_id(user["sub"])

    if db_user is None or not db_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "user_not_found", "message": "کاربر پیدا نشد"},
        )

    await repo.touch_last_seen(db_user.id)
    await session.commit()

    return MeResponse(
        user_id=str(db_user.id),
        email=db_user.email,
        capital_total=float(db_user.capital_total),
        capital_available=float(db_user.capital_available),
        capital_in_use=float(db_user.capital_in_use),
        total_trades=db_user.total_trades,
        wins=db_user.wins,
        losses=db_user.losses,
    )


@router.post("/logout", status_code=204)
async def logout() -> None:
    """Logout — JWT stateless، فقط client باید token رو پاک کنه."""
    return None


# ═══════════════════════════════════════════
# Password Reset & Verification
# ═══════════════════════════════════════════

@router.post("/forgot-password")
@limiter.limit(FORGOT_PASSWORD_LIMIT)
async def forgot_password(
    request: Request,
    response: Response,
    payload: ForgotPasswordRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """درخواست لینک بازیابی رمز عبور."""
    await request_password_reset(session, payload.email)
    return {"message": "اگر این ایمیل در سیستم ثبت شده باشد، لینک بازیابی ارسال خواهد شد."}

@router.post("/reset-password")
async def reset_pass(
    payload: ResetPasswordRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """تغییر رمز عبور با توکن."""
    success = await reset_password(session, payload.token, payload.new_password)
    if not success:
        raise HTTPException(status_code=400, detail="توکن نامعتبر یا منقضی شده است.")
    return {"message": "رمز عبور با موفقیت تغییر کرد."}

@router.post("/request-verify-email")
@limiter.limit(FORGOT_PASSWORD_LIMIT)
async def req_verify_email(
    request: Request,
    response: Response,
    payload: ForgotPasswordRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """درخواست ارسال لینک تایید ایمیل."""
    await request_email_verification(session, payload.email)
    return {"message": "لینک تایید ارسال شد."}

@router.post("/verify-email")
async def verify_email_token(
    payload: VerifyEmailRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """تایید ایمیل."""
    success = await verify_email(session, payload.token)
    if not success:
        raise HTTPException(status_code=400, detail="توکن نامعتبر یا منقضی شده است.")
    return {"message": "ایمیل با موفقیت تایید شد."}
