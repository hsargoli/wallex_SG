"""ثبت همه روت‌های v1."""

from fastapi import APIRouter

from app.presentation.api.v1 import (
    specialized_backtest,
    live_bot,
    account,
    analysis,
    auth,
    nooaah,
    backtest,
    bot,
    bots,
    guest,
    markets,
    ml_bottom,
    orders,
    paper_trading,
    paper_v2,
    paper_v3,
    profitability,
    replay,
    scalping,
    scanner,
    signals,
    simulation,
    user,
    wallex,
)

router = APIRouter(prefix="/v1")
router.include_router(markets.router)
router.include_router(analysis.router)
router.include_router(auth.router)
router.include_router(nooaah.router)
router.include_router(account.router)
router.include_router(bot.router)
router.include_router(bots.router)
router.include_router(profitability.router)
router.include_router(signals.router)
router.include_router(scanner.router)
router.include_router(backtest.router)
router.include_router(specialized_backtest.router)
router.include_router(scalping.router)
router.include_router(ml_bottom.router)
router.include_router(paper_trading.router)
router.include_router(paper_v2.router)
router.include_router(paper_v3.router)
router.include_router(guest.router)
router.include_router(replay.router)
router.include_router(live_bot.router)  # /user/live-bot/*
from app.presentation.api.v1 import order_chase  # noqa: E402
router.include_router(order_chase.router)
router.include_router(orders.router)
router.include_router(simulation.router)
router.include_router(user.router)
router.include_router(wallex.router)
