"""ثبت همه روت‌های v1."""

from fastapi import APIRouter

from app.presentation.api.v1 import (
    account,
    backtest,
    bot,
    markets,
    profitability,
    scalping,
    scanner,
    signals,
)

router = APIRouter(prefix="/v1")
router.include_router(markets.router)
router.include_router(account.router)
router.include_router(bot.router)
router.include_router(profitability.router)
router.include_router(signals.router)
router.include_router(scanner.router)
router.include_router(backtest.router)
router.include_router(scalping.router)
