"""Scalp Master Bot — اسکالپ نزولی."""

import time

from app.domain.entities.candle import Candle
from app.services.bots.base import BaseBot, BotInfo, BotStatus
from app.services.bots.scalp_master.config import ScalpMasterConfig
from app.services.bots.scalp_master.strategy import evaluate_entry


class ScalpMasterBot(BaseBot):
    """اسکالپ نزولی — خرید پس از سقوط، فروش با سود کم."""

    def __init__(self, config: ScalpMasterConfig | None = None):
        self.config = config or ScalpMasterConfig()
        self._status = BotStatus.IDLE
        self._started_at = 0

    @property
    def info(self) -> BotInfo:
        return BotInfo(
            slug="scalp_master",
            name="اسکالپ‌مستر",
            name_en="Scalp Master Bot",
            version="0.1.0",
            description="خرید پس از سقوط و فروش با سود کم (اسکالپ نزولی)",
            tags=["scalping", "dip_buy", "mean_reversion"],
            capabilities=["paper", "live", "backtest"],
        )

    @property
    def status(self) -> BotStatus:
        return self._status

    async def start(self, exchange) -> dict:
        self._status = BotStatus.RUNNING
        self._started_at = int(time.time())
        return {"status": "started", "bot": "scalp_master"}

    async def stop(self) -> dict:
        self._status = BotStatus.STOPPED
        return {"status": "stopped"}

    def reset(self) -> dict:
        self._status = BotStatus.IDLE
        self._started_at = 0
        return {"status": "reset"}

    def get_status(self) -> dict:
        return {
            "is_running": self._status == BotStatus.RUNNING,
            "started_at": self._started_at,
            "config": {
                "timeframe": self.config.timeframe,
                "drop_threshold_pct": self.config.drop_threshold_pct,
                "take_profit_pct": self.config.take_profit_pct,
                "stop_loss_pct": self.config.stop_loss_pct,
            },
        }

    def make_decision(self, symbol: str, candles: list[Candle]) -> dict | None:
        """تصمیم ورود."""
        signal = evaluate_entry(candles, self.config)
        if signal is None or not signal.should_trade:
            return None

        return {
            "should_trade": True,
            "action": signal.action,
            "entry": signal.entry_price,
            "tp": signal.take_profit,
            "sl": signal.stop_loss,
            "reason": signal.reason,
            "strategy": "scalp_master",
        }
