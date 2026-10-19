"""Dependency Injection برای FastAPI."""
import uuid
from typing import Annotated, AsyncGenerator

from fastapi import Depends, Request, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.ports.exchange import ExchangePort
from app.infrastructure.db.session import SessionLocal
from app.infrastructure.db.models.user import User
from app.infrastructure.db.repositories.user_repo import UserRepository
from app.infrastructure.exchange.wallex.client import WallexExchange
from app.core.config import get_settings
from app.core.crypto import decrypt_token, TokenDecryptError
from app.presentation.api.v1.auth import require_user_token

def get_exchange(request: Request) -> ExchangePort:
    """Exchange را از state اپ برمی‌گرداند (در lifespan ست شده)."""
    return request.app.state.exchange

ExchangeDep = Annotated[ExchangePort, Depends(get_exchange)]

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to provide a database session."""
    async with SessionLocal() as session:
        yield session

async def get_user_exchange(
    user: Annotated[dict, Depends(require_user_token)],
    session: AsyncSession = Depends(get_db_session),
) -> ExchangePort:
    """ساخت یک نمونه اختصاصی از والکس با توکن Trade کاربر."""
    try:
        user_id = uuid.UUID(user["sub"])
    except (KeyError, ValueError):
        raise HTTPException(status_code=401, detail="sub نامعتبر در توکن")

    db_user = await session.get(User, user_id)
    if not db_user or not db_user.wallex_trade_token_encrypted:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "no_trade_token", "message": "توکن Trade متصل نیست. ابتدا در تنظیمات متصل کنید."}
        )

    try:
        trade_token = decrypt_token(db_user.wallex_trade_token_encrypted).decode("utf-8")
    except TokenDecryptError:
        raise HTTPException(status_code=500, detail="خطا در رمزگشایی توکن Trade")

    settings = get_settings()
    return WallexExchange.create(settings, api_key=trade_token)

UserExchangeDep = Annotated[ExchangePort, Depends(get_user_exchange)]
