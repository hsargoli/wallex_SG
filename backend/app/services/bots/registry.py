"""Bot Registry — ثبت و کشف ربات‌ها."""

from app.services.bots.base import BaseBot, BotInfo


class BotRegistry:
    """ثبت و مدیریت همه‌ی ربات‌ها."""

    def __init__(self):
        self._bots: dict[str, BaseBot] = {}

    def register(self, bot: BaseBot) -> None:
        """ثبت یک ربات."""
        slug = bot.info.slug
        if slug in self._bots:
            raise ValueError(f"ربات '{slug}' قبلاً ثبت شده")
        self._bots[slug] = bot

    def get(self, slug: str) -> BaseBot | None:
        """دریافت یک ربات بر اساس slug."""
        return self._bots.get(slug)

    def list_all(self) -> list[BotInfo]:
        """لیست همه‌ی ربات‌ها."""
        return [bot.info for bot in self._bots.values()]

    def slugs(self) -> list[str]:
        """لیست slug های همه‌ی ربات‌ها."""
        return list(self._bots.keys())

    def __contains__(self, slug: str) -> bool:
        return slug in self._bots


# Singleton
bot_registry = BotRegistry()
