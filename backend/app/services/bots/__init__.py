"""بسته‌ی ربات‌ها — ثبت خودکار همه‌ی ربات‌ها."""

from app.services.bots.base import BaseBot, BotInfo, BotStatus
from app.services.bots.grid_bot import GridBot
from app.services.bots.mean_revert import MeanRevertBot
from app.services.bots.registry import bot_registry
from app.services.bots.smart_portfolio import SmartPortfolioBot
from app.services.bots.trend_follow import TrendFollowBot
from app.services.bots.volatility_hunter import VolatilityHunterBot
from app.services.bots.volatility_hunter_v2 import VolatilityHunterV2Bot


def _register_all():
    """ثبت همه‌ی ربات‌های موجود."""
    if "mean_revert" not in bot_registry:
        bot_registry.register(MeanRevertBot())
    if "trend_follow" not in bot_registry:
        bot_registry.register(TrendFollowBot())
    if "grid_bot" not in bot_registry:
        bot_registry.register(GridBot())
    if "volatility_hunter" not in bot_registry:
        bot_registry.register(VolatilityHunterBot())
    if "volatility_hunter_v2" not in bot_registry:
        bot_registry.register(VolatilityHunterV2Bot())
    if "smart_portfolio" not in bot_registry:
        bot_registry.register(SmartPortfolioBot())


_register_all()

__all__ = ["BaseBot", "BotInfo", "BotStatus", "bot_registry"]
