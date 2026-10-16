"""Guest Mode — endpoints حالت مهمان.

پیش‌نیاز: header `X-Guest-Token` روی همه‌ی endpointها (به‌جز anonymous).

منابع:
- docs/design/GUEST_MODE.md (v2.1)
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from pydantic import BaseModel, Field

from app.infrastructure.paper_trading.engine import PaperEngine
from app.services.guest import (
    ensure_guest_dir,
    generate_guest_token,
    guest_dir,
    guest_meta_path,
    is_valid_token,
    validate_token,
)

log = structlog.get_logger("guest.api")
router = APIRouter(prefix="/guest", tags=["Guest Mode"])

# ─── ثابت‌ها ───
DEFAULT_GUEST_CAPITAL = 500_000.0        # ۵۰۰ هزار تومان
DEFAULT_BOT = "scalp_master"
DEFAULT_SYMBOLS = ["BTCTMN", "ETHTMN", "SOLTMN"]
DEFAULT_TIMEFRAME = "1h"
DEFAULT_CHECK_INTERVAL = 180


# ═══════════════════════════════════════════
# Dependency: guest_token از header
# ═══════════════════════════════════════════

async def require_guest_token(
    x_guest_token: Annotated[str | None, Header(alias="X-Guest-Token")] = None,
) -> str:
    """گرفتن و اعتبارسنجی guest-token از header.

    چک می‌کنه:
    - header موجود باشه
    - فرمت UUID v4 باشه
    - توکن قبلاً ساخته شده باشه (پوشه‌ش وجود داره)
    """
    if not x_guest_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="هدر X-Guest-Token لازم است",
        )
    try:
        validate_token(x_guest_token)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        ) from e

    # توکن باید قبلاً ساخته شده باشه
    if not guest_dir(x_guest_token).exists():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="guest-token ناشناخته است — ابتدا /v1/guest/anonymous را صدا بزن",
        )
    return x_guest_token


# ═══════════════════════════════════════════
# Schemas
# ═══════════════════════════════════════════

class AnonymousResponse(BaseModel):
    guest_token: str
    capital_total: float
    created_at: int


class GuestMeResponse(BaseModel):
    guest_token: str
    capital_total: float
    created_at: int
    last_seen_at: int


class StartRequest(BaseModel):
    bot_slug: str = DEFAULT_BOT
    symbols: list[str] = Field(default_factory=lambda: list(DEFAULT_SYMBOLS))
    timeframe: str = DEFAULT_TIMEFRAME
    initial_capital: float = DEFAULT_GUEST_CAPITAL
    check_interval_sec: int = DEFAULT_CHECK_INTERVAL
    position_size_pct: float = 50.0


class ManualOrderRequest(BaseModel):
    """سفارش دستی مهمان (شبیه‌سازی)."""
    side: str = Field(..., pattern="^(buy|sell)$")
    symbol: str = Field(..., min_length=3)
    quantity: float = Field(..., gt=0)
    tp_pct: float = Field(default=2.0, ge=0.1, le=50)
    sl_pct: float = Field(default=1.0, ge=0.1, le=50)


# ═══════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════

def _get_or_create_meta(token: str) -> dict:
    """متادیتای مهمان رو بخون یا آپدیت کن (پوشه باید از قبل باشه)."""
    # پوشه از قبل توسط /anonymous ساخته شده
    meta_path = guest_meta_path(token)
    if meta_path.exists():
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except Exception:
            meta = {}
    else:
        meta = {}

    now = int(time.time())
    if "created_at" not in meta:
        meta["created_at"] = now
    meta["last_seen_at"] = now

    meta_path.write_text(
        json.dumps(meta, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return meta


def _get_engine(request: Request, token: str) -> PaperEngine | None:
    """گرفتن engine مهمان از app.state (اگه هست)."""
    engines: dict[str, PaperEngine] = getattr(request.app.state, "guest_engines", {})
    return engines.get(token)


def _get_or_create_engine(
    request: Request,
    token: str,
    payload: StartRequest | None = None,
) -> PaperEngine:
    """گرفتن یا ساخت engine مهمان."""
    engines: dict[str, PaperEngine] = getattr(request.app.state, "guest_engines", {})
    if not hasattr(request.app.state, "guest_engines"):
        request.app.state.guest_engines = engines

    engine = engines.get(token)
    if engine is not None:
        return engine

    exchange = request.app.state.exchange
    state_dir = guest_dir(token)

    engine = PaperEngine(
        exchange=exchange,
        bot_slug=payload.bot_slug if payload else DEFAULT_BOT,
        symbols=list(payload.symbols) if payload else list(DEFAULT_SYMBOLS),
        timeframe=payload.timeframe if payload else DEFAULT_TIMEFRAME,
        initial_capital=payload.initial_capital if payload else DEFAULT_GUEST_CAPITAL,
        check_interval_sec=payload.check_interval_sec if payload else DEFAULT_CHECK_INTERVAL,
        position_size_pct=payload.position_size_pct if payload else 50.0,
        state_dir=state_dir,
    )
    engines[token] = engine
    return engine


# ═══════════════════════════════════════════
# Endpoints
# ═══════════════════════════════════════════

@router.post("/anonymous", response_model=AnonymousResponse)
async def create_anonymous() -> AnonymousResponse:
    """ساخت مهمان جدید (بدون auth).

    یه UUID v4 برمی‌گردونه که frontend توی localStorage ذخیره می‌کنه.
    """
    token = generate_guest_token()
    ensure_guest_dir(token)
    meta = _get_or_create_meta(token)

    log.info("guest.created", token=token[:8] + "...")

    return AnonymousResponse(
        guest_token=token,
        capital_total=DEFAULT_GUEST_CAPITAL,
        created_at=meta["created_at"],
    )


@router.get("/me", response_model=GuestMeResponse)
async def get_me(
    request: Request,
    token: Annotated[str, Depends(require_guest_token)],
) -> GuestMeResponse:
    """اطلاعات مهمان."""
    meta = _get_or_create_meta(token)
    return GuestMeResponse(
        guest_token=token,
        capital_total=DEFAULT_GUEST_CAPITAL,
        created_at=meta["created_at"],
        last_seen_at=meta["last_seen_at"],
    )


@router.get("/paper-v3/status")
async def get_paper_status(
    request: Request,
    token: Annotated[str, Depends(require_guest_token)],
) -> dict:
    """وضعیت paper مهمان."""
    _get_or_create_meta(token)
    engine = _get_engine(request, token)
    if engine is None:
        return {
            "is_running": False,
            "initial_capital": DEFAULT_GUEST_CAPITAL,
            "capital": DEFAULT_GUEST_CAPITAL,
            "equity": DEFAULT_GUEST_CAPITAL,
            "peak_capital": DEFAULT_GUEST_CAPITAL,
            "peak_equity": DEFAULT_GUEST_CAPITAL,
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
            "started_at": 0,
            "last_check_at": 0,
            "check_count": 0,
            "config": {},
        }
    return engine.get_status()


@router.get("/paper-v3/live")
async def get_paper_live(
    request: Request,
    token: Annotated[str, Depends(require_guest_token)],
) -> dict:
    """وضعیت + قیمت لحظه‌ای (PnL شناور)."""
    _get_or_create_meta(token)
    engine = _get_engine(request, token)
    if engine is None:
        return {
            "is_running": False,
            "equity": DEFAULT_GUEST_CAPITAL,
            "total_pnl": 0.0,
            "total_pnl_pct": 0.0,
            "open_positions": [],
        }
    await engine.refresh_prices()
    return engine.get_status()


@router.post("/paper-v3/start")
async def start_paper(
    request: Request,
    token: Annotated[str, Depends(require_guest_token)],
    payload: StartRequest | None = None,
) -> dict:
    """شروع paper trading مهمان."""
    _get_or_create_meta(token)

    # اگه engine در حال اجراست، اول متوقف کن
    old = _get_engine(request, token)
    if old is not None and old.state.is_running:
        await old.stop()

    engine = _get_or_create_engine(request, token, payload)
    result = await engine.start()
    log.info("guest.paper.started", token=token[:8] + "...", result=result)
    return result


@router.post("/paper-v3/stop")
async def stop_paper(
    request: Request,
    token: Annotated[str, Depends(require_guest_token)],
) -> dict:
    """توقف paper مهمان."""
    engine = _get_engine(request, token)
    if engine is None:
        return {"status": "stopped"}
    result = await engine.stop()
    log.info("guest.paper.stopped", token=token[:8] + "...")
    return result


@router.post("/order")
async def place_manual_order(
    request: Request,
    payload: ManualOrderRequest,
    token: Annotated[str, Depends(require_guest_token)],
) -> dict:
    """ثبت سفارش دستی مهمان (شبیه‌سازی).

    ⚠️ این سفارش در orderbook واقعی والکس ثبت نمی‌شه.
    فقط توی state مهمان (شبیه‌سازی) ذخیره می‌شه.
    """
    _get_or_create_meta(token)
    engine = _get_or_create_engine(request, token)

    result = await engine.execute_manual_order(
        side=payload.side,
        symbol=payload.symbol,
        quantity=payload.quantity,
        tp_pct=payload.tp_pct,
        sl_pct=payload.sl_pct,
    )

    log.info(
        "guest.manual_order",
        token=token[:8] + "...",
        side=payload.side,
        symbol=payload.symbol,
        quantity=payload.quantity,
        result=result.get("status"),
    )

    return result


@router.post("/position/{symbol}/close")
async def close_manual_position(
    request: Request,
    symbol: str,
    token: Annotated[str, Depends(require_guest_token)],
) -> dict:
    """بستن دستی پوزیشن مهمان."""
    _get_or_create_meta(token)
    engine = _get_engine(request, token)
    if engine is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="پوزیشنی برای مهمان وجود ندارد",
        )

    result = await engine.close_position(symbol)
    log.info(
        "guest.manual_close",
        token=token[:8] + "...",
        symbol=symbol,
        result=result.get("status"),
    )
    return result


@router.post("/paper-v3/reset")
async def reset_paper(
    request: Request,
    token: Annotated[str, Depends(require_guest_token)],
) -> dict:
    """ریست paper مهمان."""
    _get_or_create_meta(token)
    engine = _get_engine(request, token)
    if engine is None:
        return {"status": "no_engine"}
    result = engine.reset()
    log.info("guest.paper.reset", token=token[:8] + "...")
    return result
