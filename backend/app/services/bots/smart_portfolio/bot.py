"""Smart Portfolio Bot — پورتفوی هوشمند.

این ربات خودش تصمیم نمی‌گیره.
فقط:
  ۱. رژیم بازار رو تشخیص می‌ده
  ۲. ربات‌های مناسب رو انتخاب می‌کنه
  ۳. سرمایه رو بین‌شون تقسیم می‌کنه

سپس هر ربات جداگانه تصمیم ورود/خروج می‌گیره.
"""

import time
from dataclasses import dataclass, field
from typing import Any

from app.domain.entities.candle import Candle
from app.services.bots.base import BaseBot, BotInfo, BotStatus
from app.services.bots.smart_portfolio.allocator import (
    AllocationPlan,
    allocate,
)
from app.services.bots.smart_portfolio.config import SmartPortfolioConfig


@dataclass
class PortfolioState:
    is_running: bool = False
    total_capital: float = 300_000.0
    current_plan: dict[str, Any] | None = None
    started_at: int = 0
    last_rebalance: int = 0
    regime_changes: list[dict] = field(default_factory=list)
    active_slots: list[dict] = field(default_factory=list)


class SmartPortfolioBot(BaseBot):
    """پورتفوی هوشمند — مدیر ربات‌های دیگر."""

    def __init__(self, config: SmartPortfolioConfig | None = None):
        self.config = config or SmartPortfolioConfig()
        self.state = PortfolioState(total_capital=self.config.total_capital)
        self._status = BotStatus.IDLE

    @property
    def info(self) -> BotInfo:
        return BotInfo(
            slug="smart_portfolio",
            name="پورتفوی هوشمند",
            name_en="Smart Portfolio Bot",
            version="0.1.0",
            description="مدیریت ۴ ربات بر اساس رژیم بازار (کف‌زن، روندرو، شبکه‌ای، نوسان‌گیر)",
            tags=["meta", "portfolio", "regime_based", "multi_strategy"],
            capabilities=["paper", "live", "backtest"],
        )

    @property
    def status(self) -> BotStatus:
        return self._status

    async def start(self, exchange) -> dict:
        self._status = BotStatus.RUNNING
        self.state.is_running = True
        if self.state.started_at == 0:
            self.state.started_at = int(time.time())
        return {"status": "started", "bot": "smart_portfolio"}

    async def stop(self) -> dict:
        self._status = BotStatus.STOPPED
        self.state.is_running = False
        return {"status": "stopped"}

    def reset(self) -> dict:
        self.state = PortfolioState(total_capital=self.config.total_capital)
        self._status = BotStatus.IDLE
        return {"status": "reset"}

    def get_status(self) -> dict:
        s = self.state
        runtime_min = (int(time.time()) - s.started_at) // 60 if s.started_at else 0
        return {
            "is_running": s.is_running,
            "started_at": s.started_at,
            "runtime_minutes": runtime_min,
            "total_capital": s.total_capital,
            "current_regime": (s.current_plan or {}).get("regime"),
            "regime_confidence": (s.current_plan or {}).get("regime_confidence"),
            "active_slots": s.active_slots,
            "last_rebalance": s.last_rebalance,
            "regime_changes_count": len(s.regime_changes),
            "recent_regime_changes": s.regime_changes[:5],
            "config": {
                "timeframe": self.config.timeframe,
                "max_concurrent_bots": self.config.max_concurrent_bots,
                "rebalance_interval_min": self.config.rebalance_interval_min,
            },
        }

    def get_plan_for_symbol(
        self,
        symbol: str,
        candles: list[Candle],
    ) -> AllocationPlan:
        """تشخیص رژیم و تخصیص برای یک نماد."""
        return allocate(
            candles,
            total_capital=self.state.total_capital,
            config=self.config,
        )

    def update_plan(self, plan: AllocationPlan) -> None:
        """ذخیره‌ی پلن جدید."""
        self.state.current_plan = {
            "regime": plan.regime,
            "regime_confidence": plan.regime_confidence,
            "regime_reasons": plan.regime_reasons,
            "is_safe": plan.is_safe,
        }
        self.state.active_slots = [
            {
                "bot_slug": slot.bot_slug,
                "weight": slot.weight,
                "capital": slot.capital_allocated,
                "reason": slot.reason,
            }
            for slot in plan.slots
        ]
        self.state.last_rebalance = int(time.time())
        self.state.regime_changes.insert(
            0,
            {
                "time": int(time.time()),
                "regime": plan.regime,
                "slots": [s.bot_slug for s in plan.slots],
            },
        )
        self.state.regime_changes = self.state.regime_changes[:20]

    def make_decision(
        self,
        symbol: str,
        candles: list[Candle],
    ) -> dict | None:
        """
        برای Portfolio، "تصمیم" یعنی تخصیص رژیم.
        تصمیم‌گیری ورود/خروج واقعی توسط ربات‌های member انجام می‌شه.
        """
        plan = self.get_plan_for_symbol(symbol, candles)
        self.update_plan(plan)

        if not plan.is_safe or not plan.slots:
            return None

        return {
            "should_trade": False,  # ربات Portfolio خودش ترید نمی‌کنه
            "action": "route",
            "regime": plan.regime,
            "confidence": plan.regime_confidence,
            "allocated_bots": [
                {
                    "bot_slug": slot.bot_slug,
                    "weight": slot.weight,
                    "capital": slot.capital_allocated,
                }
                for slot in plan.slots
            ],
            "reason": f"رژیم {plan.regime}",
            "strategy": "smart_portfolio",
        }
