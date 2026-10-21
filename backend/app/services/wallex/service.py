"""Wallex connection service — اعتبارسنجی + رمزنگاری + ذخیره.

منطق business:
- connect: validate via get_balances → encrypt → save
- disconnect: clear token
- status: if connected, fetch balances (graceful errors)

Per ADR 0017.
"""

from __future__ import annotations

import asyncio
import uuid
from decimal import Decimal
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
from app.services.wallex.cost_basis import compute_cost_basis

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
    import time
    _start_time = time.time()
    try:
        balances = await exchange.get_balances()
        _elapsed = time.time() - _start_time
        log.info("wallex.connect_balances_success", elapsed_seconds=round(_elapsed, 2))
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


async def disconnect_trade_token(
    session: AsyncSession,
    user_id: uuid.UUID,
) -> None:
    """قطع اتصال توکن معاملات."""
    repo = UserRepository(session)
    db_user = await repo.get_by_id(user_id)
    if db_user is None:
        raise WallexError("user_not_found", "کاربر پیدا نشد", 404)

    await repo.set_wallex_trade_token(user_id, None)
    log.info("wallex.trade_disconnected", user_id=str(user_id)[:8])



async def connect_trade_token(
    session: AsyncSession,
    user_id: uuid.UUID,
    plaintext: str,
) -> ConnectResult:
    """ذخیره توکن معاملات (Trade)."""
    repo = UserRepository(session)
    db_user = await repo.get_by_id(user_id)
    if db_user is None:
        raise WallexError("user_not_found", "کاربر پیدا نشد", 404)

    settings = get_settings()
    exchange = WallexExchange.create(settings, api_key=plaintext)
    try:
        balances = await exchange.get_balances()
    except Exception as e:
        log.warning("wallex.connect_trade_invalid", user_id=str(user_id)[:8], error=str(e))
        raise WallexError("invalid_token", "توکن وارد شده نامعتبر است یا دسترسی معامله ندارد.", 400)

    encrypted = encrypt_token(plaintext)
    await repo.set_wallex_trade_token(user_id, encrypted)
    await session.commit()

    return ConnectResult(
        connected=True,
        connected_at=datetime.now(timezone.utc),
        balances=_balances_to_dict(balances),
    )


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

    trade_connected = bool(db_user.wallex_trade_token_encrypted)
    trade_connected_at = (
        db_user.wallex_trade_connected_at.isoformat()
        if db_user.wallex_trade_connected_at
        else None
    )

    has_view = bool(db_user.wallex_token_encrypted)
    has_trade = bool(db_user.wallex_trade_token_encrypted)
    is_connected = has_view or has_trade

    if not is_connected:
        return {
            "connected": False,
            "view_connected": False,
            "trade_connected": False,
            "connected_at": None,
            "balances": None,
            "trade_connected_at": None,
            "is_trading_enabled": db_user.is_trading_enabled,
        }

    # TODO: Add unit test for Trade-only fallback (Phase 2)
    # اگر توکن ویو نبود، از توکن ترید برای خواندن موجودی استفاده می‌کنیم
    token_to_use = db_user.wallex_token_encrypted if has_view else db_user.wallex_trade_token_encrypted
    connected_at_val = db_user.wallex_connected_at if has_view else db_user.wallex_trade_connected_at
    connected_at = (
        connected_at_val.isoformat()
        if hasattr(connected_at_val, 'isoformat')
        else None
    )

    # decrypt
    try:
        plaintext = decrypt_token(token_to_use)
    except TokenDecryptError:
        log.warning("wallex.decrypt_failed", user_id=str(user_id)[:8])
        return {
            "connected": True,
            "view_connected": has_view,
            "trade_connected": has_trade,
            "connected_at": connected_at,
            "balances": None,
            "error": "decrypt_failed",
            "trade_connected_at": trade_connected_at,
            "is_trading_enabled": db_user.is_trading_enabled,
        }

    # fetch balances
    settings = get_settings()
    exchange = WallexExchange.create(settings, api_key=plaintext)
    try:
        balances = await exchange.get_balances()
        return {
            "connected": True,
            "view_connected": has_view,
            "trade_connected": has_trade,
            "connected_at": connected_at,
            "balances": _balances_to_dict(balances),
            "trade_connected": has_trade,
            "trade_connected_at": trade_connected_at,
        }
    except Exception as e:
        log.warning("wallex.get_balances_failed", user_id=str(user_id)[:8], error=str(e))
        return {
            "connected": True,
            "view_connected": has_view,
            "trade_connected": has_trade,
            "connected_at": connected_at,
            "balances": None,
            "error": "wallex_unavailable",
            "trade_connected": has_trade,
            "trade_connected_at": trade_connected_at,
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
            "view_connected": has_view,
            "trade_connected": has_trade,
            "connected_at": connected_at,
            "balances": None,
            "error": "wallex_unavailable",
        }
    finally:
        await exchange.aclose()

# ═══════════════════════════════════════════
# PnL (FIFO cost basis) — per ADR 0018
# ═══════════════════════════════════════════

import time as _time

from app.domain.entities.balance import Balance as _Balance
from app.domain.entities.order import Order as _Order


# ساده‌ترین cache in-memory: {user_id_str: (timestamp, data)}
# TODO: migrate to Redis if multi-worker
_PNL_CACHE: dict[str, tuple[float, dict]] = {}
_PNL_CACHE_TTL = 300  # 5 min per ADR 0018


def _cache_get(user_id: str) -> dict | None:
    item = _PNL_CACHE.get(user_id)
    if not item:
        return None
    ts, data = item
    if _time.time() - ts > _PNL_CACHE_TTL:
        _PNL_CACHE.pop(user_id, None)
        return None
    return data


def _cache_set(user_id: str, data: dict) -> None:
    _PNL_CACHE[user_id] = (_time.time(), data)


def _clean_num(v) -> str | None:
    """تبدیل عدد به رشته‌ی تمیز (بدون .0 اضافی).

    >>> _clean_num(10.0)
    '10'
    >>> _clean_num(10.5)
    '10.5'
    >>> _clean_num(None)
    None
    """
    if v is None:
        return None
    d = Decimal(str(v))
    if d == d.to_integral_value():
        return str(int(d))
    return str(d.normalize())


def _markets_by_symbol(orders: list[_Order]) -> list[str]:
    """استخراج symbols یکتا از سفارش‌ها."""
    return sorted({o.symbol for o in orders})


async def compute_pnl(
    session: AsyncSession,
    user_id: uuid.UUID,
) -> dict:
    """محاسبه‌ی PnL با FIFO (per ADR 0018).

    Returns:
        {
          "assets": [...],
          "summary": {...},
          "computed_at": "...",
          "cached": bool,
        }

    Raises:
        WallexError: user_not_found, invalid_token, wallex_unavailable
    """
    cache_key = str(user_id)
    cached = _cache_get(cache_key)
    if cached is not None:
        return {**cached, "cached": True}

    # ── user + token ──
    repo = UserRepository(session)
    db_user = await repo.get_by_id(user_id)
    if db_user is None:
        raise WallexError("user_not_found", "کاربر پیدا نشد", 404)
    if not db_user.wallex_token_encrypted:
        raise WallexError(
            "not_connected",
            "ابتدا به والکس متصل شو",
            400,
        )

    try:
        plaintext = decrypt_token(db_user.wallex_token_encrypted)
    except TokenDecryptError as e:
        raise WallexError(
            "decrypt_failed",
            "توکن ذخیره‌شده قابل رمزگشایی نیست — دوباره متصل شو",
            400,
        ) from e

    # ── fetch orders + balances از Wallex ──
    # (قیمت فعلی از frontend میاد — frontend useMarkets داره)
    settings = get_settings()
    exchange = WallexExchange.create(settings, api_key=plaintext)
    try:
        orders, balances = await asyncio.gather(
            exchange.get_orders(),
            exchange.get_balances(),
            return_exceptions=False,
        )
    except ExchangeAuthError as e:
        raise WallexError(
            "invalid_token", "توکن در والکس نامعتبر یا revoke شده", 400
        ) from e
    except ExchangeError as e:
        raise WallexError(
            "wallex_unavailable",
            "الان نمی‌تونیم به والکس وصل شیم — بعداً امتحان کن",
            503,
        ) from e
    finally:
        await exchange.aclose()


    # ── FIFO ──
    cost_map = compute_cost_basis(orders)

    # ── fetched balances by asset ──
    balances_by_asset: dict[str, _Balance] = {
        b.asset.upper(): b for b in balances
    }

    # ── current prices: از markets ──
    position_symbols = {
        s for s, cb in cost_map.items() if cb.total_qty > 0
    }

    # ── merge: هم assets با position، هم assets در balances ──
    all_symbols = sorted(
        position_symbols.union(
            {f"{a}TMN" for a in balances_by_asset if a != "TMN"}
        )
    )

    assets_result: list[dict] = []
    total_cost = 0.0
    total_value = 0.0
    unknown_count = 0

    for symbol in all_symbols:
        # asset code (PEPETMN → PEPE)
        asset = symbol[:-3] if symbol.endswith("TMN") else symbol
        cb = cost_map.get(symbol)
        balance = balances_by_asset.get(asset)
        qty_balance = float(balance.total) if balance else 0.0
        qty_fifo = float(cb.total_qty) if cb else 0.0

        # اگه balance > 0 ولی FIFO خالی → buy قبل از تاریخچه
        if qty_balance > 0 and qty_fifo == 0:
            has_unknown = True
        else:
            has_unknown = cb.has_unknown_history if cb else False

        avg_cost = float(cb.avg_cost) if cb and qty_fifo > 0 else None
        cost = float(cb.total_cost) if cb else 0.0
        # قیمت فعلی و current_value از frontend میان (نه backend)
        current_price = None
        current_value = None

        # PnL فقط اگه همه‌ی اجزا موجود باشن
        unrealized_pnl = None
        unrealized_pnl_pct = None
        if (
            not has_unknown
            and avg_cost is not None
            and current_value is not None
            and cost > 0
        ):
            unrealized_pnl = current_value - cost
            unrealized_pnl_pct = (unrealized_pnl / cost) * 100

        # total_value همیشه (حتی برای unknown) چون کاربر می‌خواد ببینه "الان چقدر می‌ارزه"
        if has_unknown:
            unknown_count += 1
            if current_value is not None:
                total_value += current_value
        else:
            total_cost += cost
            if current_value is not None:
                total_value += current_value

        assets_result.append({
            "asset": asset,
            "symbol": symbol,
            "total_qty": _clean_num(balance.total) if balance else _clean_num(cb.total_qty if cb else 0),
            "avg_cost": _clean_num(avg_cost),
            "total_cost": _clean_num(cost),
            "current_price": _clean_num(current_price),
            "current_value": _clean_num(current_value),
            "unrealized_pnl": _clean_num(unrealized_pnl),
            "unrealized_pnl_pct": _clean_num(unrealized_pnl_pct),
            "has_unknown_history": has_unknown,
        })

    # مرتب‌سازی: ارزش نزولی
    assets_result.sort(
        key=lambda a: float(a["current_value"] or 0),
        reverse=True,
    )

    summary = {
        "total_cost": _clean_num(total_cost),
        "total_value": _clean_num(total_value),
        "total_pnl": _clean_num(total_value - total_cost) if total_cost > 0 else "0",
        "total_pnl_pct": _clean_num(
            ((total_value - total_cost) / total_cost * 100)
            if total_cost > 0 else 0
        ),
        "assets_with_unknown_history": unknown_count,
    }

    result = {
        "assets": assets_result,
        "summary": summary,
        "computed_at": datetime.now(timezone.utc).isoformat(),
    }
    _cache_set(cache_key, result)
    return {**result, "cached": False}

