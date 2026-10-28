"""Test-first: Nooaah must inherit BaseBot, and registry must support tiers."""
import pytest
from app.services.bots.base import BaseBot, BotInfo
from app.services.bots.nooaah.bot import NooaahBot
from unittest.mock import MagicMock

class TestBotArchitecture:
    def test_nooaah_inherits_basebot(self):
        assert issubclass(NooaahBot, BaseBot), "NooaahBot must inherit from BaseBot"

    def test_nooaah_is_registered_with_production_tier(self):
        ex = MagicMock()
        bot = NooaahBot(exchange=ex)
        assert bot.info.tier == "production"
        assert bot.info.slug == "nooaah"

    def test_registry_tier_filtering(self):
        info = BotInfo(slug="test", name="t", name_en="t", version="1", description="t")
        assert hasattr(info, "tier")
        assert info.tier == "experimental"  # default
