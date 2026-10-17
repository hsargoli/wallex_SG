"""Wallex connection service — اعتبارسنجی + رمزنگاری + ذخیره.

منطق business:
- connect: validate via get_balances → encrypt → save
- disconnect: clear token
- status: if connected, fetch balances (graceful errors)

Per ADR 0017.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.crypto import TokenDecryptError, decrypt_token, encrypt_token
from app.domain.entities.balance import Balance
from app.domain.exceptions import ExchangeAuthError, ExchangeError
from app.infrastructure.db.repositories import UserRepository
from app.infrastructure.exchange.wallex.client import WallexExchange

log = structlog.get_logger("wallex.service")


class WallexError(Exception):
    """خطای wallex — با code و status برای تبدیل به HTTPException."""

    def __init__(self, code: str, message: str, status: int = 400):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status


@dataclass
class ConnectResult:
    connected: bool
    connected_at: str
    balances: list[dict]

    def to_dict(self) -> dict:
        return {
            "connected": self.connected,
            "connected_at": self.connected_at,
            "balances": self.balances,
        }


def _balances_to_dict(balances: list[Balance]) -> list[dict]:
    return [
        {
            "asset": b.asset,
            "available": str(b.available),
            "locked": str(b.locked),
            "total": str(b.total),
            "fa_name": b.fa_name,
            "en_name": b.en_name,
        }
        for b in balances
    ]


async def connect_token(
    session: AsyncSession,
    user_id: uuid.UUID,
    plaintext_token: str,
) -> ConnectResult:
    """اعتبارسنجی + رمزنگاری + ذخیره‌ی توکن Wallex.

    Raises:
        WallexError: user_not_found (404), invalid_token (400), wallex_unavailable (503)
    """
    repo = UserRepository(session)
    db_user = await repo.get_by_id(user_id)
    if db_user is None:
        raise WallexError("user_not_found", "کاربر پیدا نشد", 404)

    # ── اعتبارسنجی: با توکن کاربر، موجودی‌ها رو بگیر ──
    settings = get_settings()
    exchange = WallexExchange.create(settings, api_key=plaintext_token)
    try:
        balances = await exchange.get_balances()
    except ExchangeAuthError as e:
        log.info("wallex.connect_invalid_token", user_id=str(user_id)[:8])
        raise WallexError(
            "invalid_token", "توکن نامعتبر یا منقضی است", 400
        ) from e
    except ExchangeError as e:
        log.info(
            "wallex.connect_unavailable",
            user_id=str(user_id)[:8],
            error=str(e),
        )
        raise WallexError(
            "wallex_unavailable",
            "الان نمی‌تونیم به والکس وصل شیم — بعداً امتحان کن",
            503,
        ) from e
    finally:
        await exchange.aclose()

    # ── رمزنگاری + ذخیره ──
    encrypted = encrypt_token(plaintext_token)
    await repo.set_wallex_token(user_id, encrypted)

    connected_at = datetime.now(timezone.utc).isoformat()
    log.info(
        "wallex.connected",
        user_id=str(user_id)[:8],
        balance_count=len(balances),
    )

    return ConnectResult(
        connected=True,
        connected_at=connected_at,
        balances=_balances_to_dict(balances),
    )


async def disconnect_token(
    session: AsyncSession,
    user_id: uuid.UUID,
) -> None:
    """قطع اتصال — فقط توکن پاک می‌شه، تاریخچه می‌مونه."""
    repo = UserRepository(session)
    db_user = await repo.get_by_id(user_id)
    if db_user is None:
        raise WallexError("user_not_found", "کاربر پیدا نشد", 404)

    await repo.set_wallex_token(user_id, None)
    log.info("wallex.disconnected", user_id=str(user_id)[:8])


async def get_status(
    session: AsyncSession,
    user_id: uuid.UUID,
) -> dict:
    """وضعیت اتصال + موجودی (اگه وصل باشه).

    اگه توکن decrypt نشه یا revoke شده باشه، error برمی‌گردونه
    ولی connected=True می‌مونه (چون توکن هنوز ذخیره شده).
    """
    repo = UserRepository(session)
    db_user = await repo.get_by_id(user_id)
    if db_user is None:
        raise WallexError("user_not_found", "کاربر پیدا نشد", 404)

    if not db_user.wallex_token_encrypted:
        return {
            "connected": False,
            "connected_at": None,
            "balances": None,
        }

    connected_at = (
        db_user.wallex_connected_at.isoformat()
        if db_user.wallex_connected_at
        else None
    )

    # decrypt
    try:
        plaintext = decrypt_token(db_user.wallex_token_encrypted)
    except TokenDecryptError:
        log.warning("wallex.decrypt_failed", user_id=str(user_id)[:8])
        return {
            "connected": True,
            "connected_at": connected_at,
            "balances": None,
            "error": "decrypt_failed",
        }

    # fetch balances
    settings = get_settings()
    exchange = WallexExchange.create(settings, api_key=plaintext)
    try:
        balances = await exchange.get_balances()
        return {
            "connected": True,
            "connected_at": connected_at,
            "balances": _balances_to_dict(balances),
        }
    except ExchangeAuthError:
        return {
            "connected": True,
            "connected_at": connected_at,
            "balances": None,
            "error": "token_revoked",
        }
    except ExchangeError:
        return {
            "connected": True,
            "connected_at": connected_at,
            "balances": None,
            "error": "wallex_unavailable",
        }
    finally:
        await exchange.aclose()
