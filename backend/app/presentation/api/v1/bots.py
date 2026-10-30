"""Bot Registry endpoints."""
import json
from pathlib import Path

from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Request, status
from app.presentation.api.v1.auth import require_user_token
from app.infrastructure.db.session import SessionLocal
from app.infrastructure.db.models.user_bot_config import UserBotConfig
from sqlalchemy import select
import uuid as _uuid
from decimal import Decimal as _Decimal

from app.domain.models.budget import (
    BotBudgetListResponse,
    BotBudgetResponse,
    BotBudgetUpdateRequest,
    TotalBudgetResponse,
)
from app.services.bots import bot_registry
from app.services.budget_service import budget_service

router = APIRouter(prefix="/bots", tags=["Bots"])

# ============================================================
# Bot Budget Endpoints
# ============================================================


@router.get(
    "/list",
    summary="لیست ربات‌ها (قابل فیلتر بر اساس tier)",
)
async def list_bots(tier: str | None = None):
    """لیست همه‌ی ۱۱ ربات (scheduler + registry + archived stubs)."""
    items = []

    for slug, info in _SCHEDULER_BOTS.items():
        items.append({
            "slug": slug,
            "tier": "production",
            "name": info["name"],
            "name_en": info["name_en"],
            "archived": False,
        })

    for info in bot_registry.list_all():
        items.append({
            "slug": info.slug,
            "tier": info.tier,
            "name": info.name,
            "name_en": info.name_en,
            "archived": info.slug in _ARCHIVED_SET,
        })

    for slug, info in _ARCHIVED_STUBS.items():
        items.append({
            "slug": slug,
            "tier": "experimental",
            "name": info["name"],
            "name_en": info["name_en"],
            "archived": True,
        })

    if tier:
        items = [x for x in items if x["tier"] == tier]
    return {"count": len(items), "items": items}

@router.get(
    "/budgets",
    response_model=BotBudgetListResponse,
    summary="لیست بودجه‌ی همه ربات‌ها",
)
async def list_bot_budgets():
    """لیست بودجه‌ی همه‌ی ربات‌های دارای تخصیص."""
    items = budget_service.list_bot_allocations()
    return BotBudgetListResponse(
        count=len(items),
        items=[BotBudgetResponse(**item) for item in items],
    )


@router.get(
    "/budgets/total",
    response_model=TotalBudgetResponse,
    summary="وضعیت کلی بودجه",
)
async def get_total_budget():
    """وضعیت کلی بودجه — برای صفحه‌ی کیف پول ربات."""
    s = budget_service.get_status()
    return TotalBudgetResponse(
        total_budget=s["total_budget"],
        total_allocated=s["total_allocated"],
        unallocated=s["unallocated"],
        total_in_use=s["total_in_use"],
        available=s["available"],
        allocated_budget=s["allocated_budget"],
        in_use_capital=s["in_use_capital"],
        available_for_trade=s["available_for_trade"],
    )


@router.get(
    "/{slug}/budget",
    response_model=BotBudgetResponse,
    summary="بودجه‌ی یک ربات",
)
async def get_bot_budget(slug: str):
    """دریافت بودجه‌ی اختصاصی یک ربات."""
    bot = bot_registry.get(slug)
    if bot is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ربات '{slug}' پیدا نشد",
        )
    status_dict = budget_service.get_bot_status(slug)
    return BotBudgetResponse(**status_dict)


@router.post(
    "/{slug}/budget",
    response_model=BotBudgetResponse,
    summary="تخصیص بودجه به یک ربات",
)
async def set_bot_budget(slug: str, payload: BotBudgetUpdateRequest):
    """تعیین/به‌روزرسانی بودجه‌ی اختصاصی یک ربات."""
    bot = bot_registry.get(slug)
    if bot is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ربات '{slug}' پیدا نشد",
        )
    try:
        budget_service.set_bot_allocation(slug, payload.allocated)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e
    status_dict = budget_service.get_bot_status(slug)
    return BotBudgetResponse(**status_dict)



@router.get("")
async def list_bots():
    """لیست همه‌ی ربات‌ها."""
    return {
        "count": len(bot_registry.slugs()),
        "bots": [
            {
                "slug": info.slug,
                "name": info.name,
                "name_en": info.name_en,
                "version": info.version,
                "description": info.description,
                "tags": info.tags,
                "capabilities": info.capabilities,
                "author": info.author,
            }
            for info in bot_registry.list_all()
        ],
    }


def _load_bot_report(slug: str, kind: str) -> dict:
    """Load per-bot report JSON (backtest/paper/meta). Fail-safe."""
    p = Path("data") / "bots" / slug / f"{kind}.json"
    try:
        if p.exists():
            return json.loads(p.read_text())
    except Exception:
        pass
    return {"status": "no_data"}


# Bots not in registry but shown on platform (scheduler-based)
_ARCHIVED_SET = {
    "grid_bot", "market_scanner", "mean_revert", "trend_follow",
    "volatility_hunter", "volatility_hunter_v2", "smart_portfolio",
    "sarv_tiger", "scalp_master",
}

_SCHEDULER_BOTS = {
    "nooaah": {
        "name": "نوح",
        "name_en": "Nooaah",
        "version": "1.0",
        "description": "ربات ML-based، regime-aware، multi-symbol",
        "tags": ["ml", "regime_based", "multi_symbol"],
        "capabilities": ["paper", "live", "backtest"],
        "author": "ROSHD_SARV",
        "status": "running",
    },
    "sarv_router": {
        "name": "سرو‌روتر",
        "name_en": "SarvRouter",
        "version": "1.0",
        "description": "روتر رژیم-آگاه — ۲۴/۷ روی سرور، capital protection",
        "tags": ["regime_based", "multi_symbol", "router"],
        "capabilities": ["paper", "live", "backtest"],
        "author": "ROSHD_SARV",
        "status": "running",
    },
}

_ARCHIVED_STUBS = {
    "sarv_tiger": {
        "name": "ببر سرو",
        "name_en": "SarvTiger",
        "version": "0.1.0",
        "description": "Bollinger Squeeze + تحلیل‌گر تاریخی (آرشیو — edge ندارد)",
        "tags": ["bollinger", "squeeze", "swing"],
        "capabilities": ["backtest"],
        "author": "ROSHD_SARV",
        "status": "stopped",
    },
    "scalp_master": {
        "name": "اسکالپ مستر",
        "name_en": "Scalp Master",
        "version": "0.1.0",
        "description": "اسکالپ روی نمادهای پرنوسان (آرشیو — ۳ استراتژی، همه منفی)",
        "tags": ["scalping", "momentum"],
        "capabilities": ["backtest"],
        "author": "ROSHD_SARV",
        "status": "stopped",
    },
}


@router.get("/{slug}")
async def get_bot_info(slug: str):
    """اطلاعات یک ربات + backtest + paper + meta + archived."""
    reports = {
        "backtest": _load_bot_report(slug, "backtest"),
        "paper": _load_bot_report(slug, "paper"),
        "meta": _load_bot_report(slug, "meta"),
    }

    bot = bot_registry.get(slug)
    if bot is not None:
        info = bot.info
        return {
            "slug": info.slug,
            "name": info.name,
            "name_en": info.name_en,
            "version": info.version,
            "description": info.description,
            "tags": info.tags,
            "capabilities": info.capabilities,
            "author": info.author,
            "status": bot.status.value,
            "archived": info.slug in _ARCHIVED_SET,
            **reports,
        }

    if slug in _SCHEDULER_BOTS:
        info = _SCHEDULER_BOTS[slug]
        return {"slug": slug, **info, "archived": False, **reports}

    if slug in _ARCHIVED_STUBS:
        info = _ARCHIVED_STUBS[slug]
        return {"slug": slug, **info, "archived": True, **reports}

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"ربات '{slug}' پیدا نشد",
    )

@router.get("/{slug}/status")
async def get_bot_status(
    slug: str,
    user: Annotated[dict, Depends(require_user_token)],
):
    """وضعیت کامل یک ربات (per-user)."""
    bot = bot_registry.get(slug)
    if bot is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ربات '{slug}' پیدا نشد",
        )
    return bot.get_status(user_id=user["sub"])


async def _ensure_user_config(user_id: str, slug: str) -> None:
    """Create default UserBotConfig if missing (paper, 300k)."""
    try:
        user_uuid = _uuid.UUID(user_id)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "invalid_sub", "message": "sub نامعتبر در توکن"},
        )
    async with SessionLocal() as session:
        res = await session.execute(
            select(UserBotConfig).where(
                UserBotConfig.user_id == user_uuid,
                UserBotConfig.bot_slug == slug,
            )
        )
        cfg = res.scalar_one_or_none()
        if cfg is None:
            cfg = UserBotConfig(
                user_id=user_uuid,
                bot_slug=slug,
                mode="paper",
                capital_allocated=_Decimal("10000000.00"),  # ۱۰ میلیون (Per Hosein 2026-10-30)
            )
            session.add(cfg)
            await session.commit()


@router.post("/{slug}/start")
async def start_bot(
    slug: str,
    request: Request,
    user: Annotated[dict, Depends(require_user_token)],
):
    """شروع یک ربات (per-user)."""
    bot = bot_registry.get(slug)
    if bot is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ربات '{slug}' پیدا نشد",
        )
    user_id = user["sub"]
    await _ensure_user_config(user_id, slug)
    exchange = request.app.state.exchange
    return await bot.start(exchange, user_id=user_id)


@router.post("/{slug}/stop")
async def stop_bot(
    slug: str,
    user: Annotated[dict, Depends(require_user_token)],
):
    """توقف یک ربات (per-user)."""
    bot = bot_registry.get(slug)
    if bot is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ربات '{slug}' پیدا نشد",
        )
    return await bot.stop(user_id=user["sub"])


@router.post("/{slug}/timeframe")
async def set_bot_timeframe(slug: str, payload: dict):
    """تغییر تایم‌فریم یک ربات (فقط برای market_scanner)."""
    bot = bot_registry.get(slug)
    if bot is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ربات '{slug}' پیدا نشد",
        )
    if not hasattr(bot, "set_timeframe"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"ربات '{slug}' از تغییر TF پشتیبانی نمی‌کند",
        )
    timeframe = payload.get("timeframe")
    if not timeframe:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="پارامتر timeframe لازم است",
        )
    return bot.set_timeframe(timeframe)


@router.post("/{slug}/symbols")
async def set_bot_symbols(slug: str, payload: dict):
    """تغییر نمادها (فقط برای scalp_master)."""
    bot = bot_registry.get(slug)
    if bot is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ربات '{slug}' پیدا نشد",
        )
    if not hasattr(bot, "set_symbols"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"ربات '{slug}' از تغییر نمادها پشتیبانی نمی‌کند",
        )
    symbols = payload.get("symbols")
    if not symbols:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="پارامتر symbols لازم است",
        )
    return bot.set_symbols(symbols)


@router.post("/{slug}/reset")
async def reset_bot(slug: str):
    """ریست یک ربات."""
    bot = bot_registry.get(slug)
    if bot is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ربات '{slug}' پیدا نشد",
        )
    return bot.reset()
