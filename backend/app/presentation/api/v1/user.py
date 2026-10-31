"""User Paper Trading endpoints — /v1/user/paper-v3/*.

فاز ۱۷.۷.۲.۵ — paper state برای کاربر لاگین‌شده.

auth: JWT از header Authorization (dependency: require_user_token)

State:
- app.state.user_engines: dict[uuid.UUID, UserPaperEngine]
- Scheduler مشترک (GuestScheduler با provider دوم) engineها رو check می‌کنه
"""

from __future__ import annotations

import uuid
from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel

from app.infrastructure.db.session import SessionLocal
from app.infrastructure.paper_trading.state import PaperState
from app.infrastructure.paper_trading.user_engine import UserPaperEngine
from app.infrastructure.paper_trading.user_repository import UserPaperRepository
from app.presentation.api.v1.auth import require_user_token

log = structlog.get_logger("user.paper_v3.api")
router = APIRouter(prefix="/user/paper-v3", tags=["User Paper V3"])


# ═══════════════════════════════════════════
# Schemas
# ═══════════════════════════════════════════

class StartRequest(BaseModel):
    bot_slug: str = "scalp_master"
    symbols: list[str] = ["NEARTMN"]
    timeframe: str = "1h"
    initial_capital: float = 10_000_000.0  # ۱۰ میلیون (Per Hosein 2026-10-30)
    check_interval_sec: int = 180
    position_size_pct: float = 50.0


class ManualOrderRequest(BaseModel):
    side: str  # "buy" | "sell"
    symbol: str
    quantity: float = 0.0
    amount_tmn: float = 0.0
    limit_price: float = 0.0
    tp_pct: float = 2.0
    sl_pct: float = 1.0


# ═══════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════

def _get_user_uuid(user: dict) -> uuid.UUID:
    """استخراج UUID از payload JWT."""
    try:
        return uuid.UUID(user["sub"])
    except (KeyError, ValueError) as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "invalid_token", "message": "sub نامعتبر در توکن"},
        ) from e


def _get_engines(request: Request) -> dict[uuid.UUID, UserPaperEngine]:
    """dict engineهای user از app.state."""
    return getattr(request.app.state, "user_engines", {})


def _get_engine(request: Request, user_id: uuid.UUID) -> UserPaperEngine | None:
    """engine کاربر اگه وجود داشته باشه."""
    return _get_engines(request).get(user_id)


def _empty_status() -> dict:
    """وضعیت پیش‌فرض وقتی engine نیست."""
    return {
        "is_running": False,
        "initial_capital": 10_000_000.0,
        "capital": 3_000_000.0,
        "equity": 3_000_000.0,
        "peak_capital": 3_000_000.0,
        "peak_equity": 3_000_000.0,
        "max_drawdown_pct": 0.0,
        "total_trades": 0,
        "wins": 0,
        "losses": 0,
        "total_pnl": 0.0,
        "total_pnl_pct": 0.0,
        "win_rate": 0.0,
        "open_positions": [],
        "recent_trades": [],
        "equity_curve": [],
        "events": [],
        "radar": [],
        "started_at": 0,
        "last_check_at": 0,
        "check_count": 0,
    }


# ═══════════════════════════════════════════
# Endpoints
# ═══════════════════════════════════════════

@router.get("/status")
async def get_status(
    request: Request,
    user: Annotated[dict, Depends(require_user_token)],
):
    """وضعیت Paper Trading کاربر."""
    user_id = _get_user_uuid(user)
    engine = _get_engine(request, user_id)
    if engine is None:
        # fallback: از DB لود کن
        repo = UserPaperRepository(user_id, SessionLocal)
        state = await repo.load()
        result = _empty_status()
        result.update(state.to_dict())
        return result
    return engine.get_status()


@router.get("/live")
async def get_live(
    request: Request,
    user: Annotated[dict, Depends(require_user_token)],
):
    """وضعیت + قیمت لحظه‌ای (PnL شناور)."""
    user_id = _get_user_uuid(user)
    engine = _get_engine(request, user_id)
    if engine is None:
        repo = UserPaperRepository(user_id, SessionLocal)
        state = await repo.load()
        result = _empty_status()
        result.update(state.to_dict())
        return result
    await engine.refresh_prices()
    return engine.get_status()


@router.post("/start")
async def start(
    request: Request,
    payload: StartRequest,
    user: Annotated[dict, Depends(require_user_token)],
):
    """شروع Paper Trading برای کاربر."""
    user_id = _get_user_uuid(user)

    # اگه engine در حال اجرا هست، اول متوقف کن
    old = _get_engine(request, user_id)
    if old is not None and old.state.is_running:
        await old.stop()

    exchange = request.app.state.exchange

    engine = UserPaperEngine(
        user_id=user_id,
        session_factory=SessionLocal,
        exchange=exchange,
        bot_slug=payload.bot_slug,
        symbols=payload.symbols,
        timeframe=payload.timeframe,
        initial_capital=payload.initial_capital,
        check_interval_sec=payload.check_interval_sec,
        position_size_pct=payload.position_size_pct,
    )

    # Per Hosein 2026-10-31: migrate stale state (e.g., old 3M capital)
    # to the intended capital. One-time safe migration: only resets if
    # state's initial_capital differs from payload.
    try:
        if await engine.repo.exists():
            _old_state = await engine.repo.load()
            if _old_state.initial_capital != payload.initial_capital:
                await engine.repo.save(PaperState.with_capital(payload.initial_capital))
                log.info(
                    "user.paper_state_migrated",
                    user_id=str(user_id)[:8],
                    old_capital=_old_state.initial_capital,
                    new_capital=payload.initial_capital,
                )
    except Exception as e:
        log.warning("user.paper_state_migrate_failed", error=str(e))

    engines = _get_engines(request)
    engines[user_id] = engine

    result = await engine.start()
    log.info("user.paper_started", user_id=str(user_id)[:8], bot=payload.bot_slug)
    return result


@router.post("/stop")
async def stop(
    request: Request,
    user: Annotated[dict, Depends(require_user_token)],
):
    """توقف Paper Trading."""
    user_id = _get_user_uuid(user)
    engine = _get_engine(request, user_id)
    if engine is None:
        return {"status": "stopped"}
    result = await engine.stop()
    log.info("user.paper_stopped", user_id=str(user_id)[:8])
    return result


@router.post("/reset")
async def reset(
    request: Request,
    user: Annotated[dict, Depends(require_user_token)],
):
    """ریست state کاربر."""
    user_id = _get_user_uuid(user)
    engine = _get_engine(request, user_id)

    if engine is not None:
        result = await engine.reset()
        log.info("user.paper_reset", user_id=str(user_id)[:8])
        return result

    # اگه engine نیست، مستقیم از repo
    # Per Hosein 2026-10-31: reset must use user's actual capital (10M)
    repo = UserPaperRepository(user_id, SessionLocal)
    await repo.save(PaperState.with_capital(10_000_000.0))
    log.info("user.paper_reset_no_engine", user_id=str(user_id)[:8])
    return {"status": "reset", "initial_capital": 10_000_000.0}


@router.post("/order")
async def place_manual_order(
    request: Request,
    payload: ManualOrderRequest,
    user: Annotated[dict, Depends(require_user_token)],
):
    """ثبت سفارش دستی کاربر (شبیه‌سازی).

    ⚠️ نیاز به Paper فعال — اگه engine نباشه، 409 Conflict.
    """
    user_id = _get_user_uuid(user)
    engine = _get_engine(request, user_id)
    if engine is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "no_engine", "message": "اول Paper را شروع کن"},
        )
    if not engine.state.is_running:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "engine_not_running",
                "message": "Paper متوقف شده — دوباره شروع کن",
            },
        )

    result = await engine.execute_manual_order(
        side=payload.side,
        symbol=payload.symbol,
        quantity=payload.quantity,
        amount_tmn=payload.amount_tmn,
        limit_price=payload.limit_price,
        tp_pct=payload.tp_pct,
        sl_pct=payload.sl_pct,
    )

    log.info(
        "user.manual_order",
        user_id=str(user_id)[:8],
        side=payload.side,
        symbol=payload.symbol,
        result=result.get("status"),
    )
    return result


@router.post("/position/{symbol}/close")
async def close_manual_position(
    request: Request,
    symbol: str,
    user: Annotated[dict, Depends(require_user_token)],
):
    """بستن دستی پوزیشن کاربر."""
    user_id = _get_user_uuid(user)
    engine = _get_engine(request, user_id)
    if engine is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "no_engine", "message": "اول Paper را شروع کن"},
        )
    if not engine.state.is_running:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "engine_not_running",
                "message": "Paper متوقف شده — دوباره شروع کن",
            },
        )

    result = await engine.close_position(symbol)
    log.info(
        "user.manual_close",
        user_id=str(user_id)[:8],
        symbol=symbol,
        result=result.get("status"),
    )
    return result
