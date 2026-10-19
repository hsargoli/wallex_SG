"""User Wallex endpoints — اتصال توکن Trade."""

from __future__ import annotations
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.presentation.api.deps import get_db_session
from app.presentation.api.v1.auth import require_user_token
from app.infrastructure.db.repositories.user_repo import UserRepository
from app.infrastructure.exchange.wallex.client import WallexExchange
from app.core.config import get_settings
from app.core.crypto import encrypt_token

router = APIRouter(prefix="/user/wallex", tags=["User Wallex"])

class ConnectTradeRequest(BaseModel):
    trade_token: str

@router.post("/connect-trade")
async def connect_trade(
    payload: ConnectTradeRequest,
    user: Annotated[dict, Depends(require_user_token)],
    session: AsyncSession = Depends(get_db_session),
):
    """اعتبارسنجی و ذخیره توکن Trade."""
    try:
        user_id = uuid.UUID(user["sub"])
    except (KeyError, ValueError):
        raise HTTPException(status_code=401, detail="توکن نامعتبر است")

    settings = get_settings()
    try:
        temp_exchange = WallexExchange.create(settings, api_key=payload.trade_token)
        await temp_exchange.get_balances()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="توکن وارد شده نامعتبر است یا دسترسی معامله ندارد."
        )

    encrypted = encrypt_token(payload.trade_token)
    repo = UserRepository(session)
    await repo.set_wallex_trade_token(user_id, encrypted)

    return {"status": "ok", "message": "توکن Trade با موفقیت ذخیره شد."}
