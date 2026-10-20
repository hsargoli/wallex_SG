"""Wallex connection endpoints — /v1/user/wallex/*.

Phase 17.8.2 — per ADR 0017.
Auth: JWT (require_user_token from auth.py)
"""

from __future__ import annotations

import uuid
from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.session import get_session
from app.infrastructure.db.models.user import User
from app.presentation.api.v1.auth import require_user_token
from app.services.wallex import (
    WallexError,
    compute_pnl,
    connect_token,
    disconnect_token,
    disconnect_trade_token,
    get_status,
)

log = structlog.get_logger("wallex.api")
router = APIRouter(prefix="/user/wallex", tags=["Wallex"])


class ConnectRequest(BaseModel):
    token: str = Field(..., min_length=10, max_length=500)
    password: str = Field(..., min_length=1)


class ConnectTradeRequest(BaseModel):
    trade_token: str = Field(..., min_length=10, max_length=500)
    password: str = Field(..., min_length=1)


def _get_user_uuid(user: dict) -> uuid.UUID:
    try:
        return uuid.UUID(user["sub"])
    except (KeyError, ValueError) as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "invalid_token", "message": "sub نامعتبر در توکن"},
        ) from e


def _to_http(e: WallexError) -> HTTPException:
    return HTTPException(
        status_code=e.status,
        detail={"code": e.code, "message": e.message},
    )


@router.post("/connect")
async def connect(
    payload: ConnectRequest,
    user: Annotated[dict, Depends(require_user_token)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    """اتصال حساب والکس با توکن View."""
    user_id = _get_user_uuid(user)
    db_user = await session.get(User, user_id)
    import bcrypt
    if not db_user or not bcrypt.checkpw(payload.password.encode("utf-8"), db_user.password_hash.encode("utf-8")):
        raise HTTPException(status_code=401, detail="رمز عبور اشتباه است")
    try:
        result = await connect_token(session, user_id, payload.token)
    except WallexError as e:
        log.info(
            "wallex.connect_failed",
            user_id=str(user_id)[:8],
            code=e.code,
        )
        raise _to_http(e) from e
    await session.commit()
    return result.to_dict()



@router.post("/connect-trade")
async def connect_trade(
    payload: ConnectTradeRequest,
    user: Annotated[dict, Depends(require_user_token)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    """اتصال توکن معاملات والکس."""
    user_id = _get_user_uuid(user)
    db_user = await session.get(User, user_id)
    import bcrypt
    if not db_user or not bcrypt.checkpw(payload.password.encode("utf-8"), db_user.password_hash.encode("utf-8")):
        raise HTTPException(status_code=401, detail="رمز عبور اشتباه است")
    try:
        from app.services.wallex.service import connect_trade_token
        result = await connect_trade_token(session, user_id, payload.trade_token)
    except WallexError as e:
        log.info("wallex.connect_trade_failed", user_id=str(user_id)[:8], code=e.code)
        raise _to_http(e) from e
    return result.to_dict()

@router.delete("/disconnect")
async def disconnect(
    user: Annotated[dict, Depends(require_user_token)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    """قطع اتصال از والکس."""
    user_id = _get_user_uuid(user)
    try:
        log.info("wallex.disconnect", user_id=str(user_id)[:8])
        await disconnect_token(session, user_id)
    except WallexError as e:
        raise _to_http(e) from e
    await session.commit()
    return {"connected": False}


@router.delete("/disconnect-trade")
async def disconnect_trade(
    user: Annotated[dict, Depends(require_user_token)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    """قطع اتصال توکن معاملات."""
    user_id = _get_user_uuid(user)
    try:
        await disconnect_trade_token(session, user_id)
    except WallexError as e:
        raise _to_http(e) from e
    await session.commit()
    return {"trade_connected": False}


@router.get("/status")
async def status(
    user: Annotated[dict, Depends(require_user_token)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    """وضعیت اتصال + موجودی‌های واقعی (اگه وصل باشه)."""
    user_id = _get_user_uuid(user)
    try:
        return await get_status(session, user_id)
    except WallexError as e:
        raise _to_http(e) from e


@router.get("/pnl")
async def pnl(
    user: Annotated[dict, Depends(require_user_token)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    """سود/زیان واقعی هر دارایی (FIFO cost basis).

    Per ADR 0018. Cache 5 min.
    """
    user_id = _get_user_uuid(user)
    try:
        return await compute_pnl(session, user_id)
    except WallexError as e:
        raise _to_http(e) from e
