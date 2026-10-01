"""Bot Registry endpoints."""

from fastapi import APIRouter, HTTPException, Request, status

from app.services.bots import bot_registry

router = APIRouter(prefix="/bots", tags=["Bots"])


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


@router.get("/{slug}")
async def get_bot_info(slug: str):
    """اطلاعات یک ربات."""
    bot = bot_registry.get(slug)
    if bot is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ربات '{slug}' پیدا نشد",
        )
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
    }


@router.get("/{slug}/status")
async def get_bot_status(slug: str):
    """وضعیت کامل یک ربات."""
    bot = bot_registry.get(slug)
    if bot is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ربات '{slug}' پیدا نشد",
        )
    return bot.get_status()


@router.post("/{slug}/start")
async def start_bot(slug: str, request: Request):
    """شروع یک ربات."""
    bot = bot_registry.get(slug)
    if bot is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ربات '{slug}' پیدا نشد",
        )
    exchange = request.app.state.exchange
    return await bot.start(exchange)


@router.post("/{slug}/stop")
async def stop_bot(slug: str):
    """توقف یک ربات."""
    bot = bot_registry.get(slug)
    if bot is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ربات '{slug}' پیدا نشد",
        )
    return await bot.stop()


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
