"""ثبت همه روت‌های v1."""

from fastapi import APIRouter

from app.presentation.api.v1 import account, bot, markets, profitability

router = APIRouter(prefix="/v1")
router.include_router(markets.router)
router.include_router(account.router)
router.include_router(bot.router)
router.include_router(profitability.router)
