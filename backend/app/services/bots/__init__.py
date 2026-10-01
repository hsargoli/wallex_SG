"""بسته‌ی ربات‌ها — ثبت خودکار همه‌ی ربات‌ها."""

from app.services.bots.base import BaseBot, BotInfo, BotStatus
from app.services.bots.mean_revert import MeanRevertBot
from app.services.bots.registry import bot_registry


# ثبت ربات‌ها
def _register_all():
    """ثبت همه‌ی ربات‌های موجود."""
    if "mean_revert" not in bot_registry:
        bot_registry.register(MeanRevertBot())


_register_all()

__all__ = ["BaseBot", "BotInfo", "BotStatus", "bot_registry"]
