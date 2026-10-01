"""ثبت همه روت‌های v1."""

from fastapi import APIRouter

from app.presentation.api.v1 import (
    account,
    backtest,
    bot,
    bots,
    markets,
    ml_bottom,
    paper_trading,
    paper_v2,
    profitability,
    replay,
    scalping,
    scanner,
    signals,
)

router = APIRouter(prefix="/v1")
router.include_router(markets.router)
router.include_router(account.router)
router.include_router(bot.router)
router.include_router(bots.router)
router.include_router(profitability.router)
router.include_router(signals.router)
router.include_router(scanner.router)
router.include_router(backtest.router)
router.include_router(scalping.router)
router.include_router(ml_bottom.router)
router.include_router(paper_trading.router)
router.include_router(paper_v2.router)
router.include_router(replay.router)
