"""Smart Portfolio — پورتفوی هوشمند."""

from app.services.bots.smart_portfolio.allocator import (
    AllocationPlan,
    BotSlot,
    allocate,
    explain_plan,
)
from app.services.bots.smart_portfolio.bot import SmartPortfolioBot
from app.services.bots.smart_portfolio.config import (
    BotAllocation,
    SmartPortfolioConfig,
)

__all__ = [
    "AllocationPlan",
    "BotAllocation",
    "BotSlot",
    "SmartPortfolioBot",
    "SmartPortfolioConfig",
    "allocate",
    "explain_plan",
]
