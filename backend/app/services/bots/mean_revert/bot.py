"""Mean Revert Bot — کف‌زن.

استراتژی:
  - کف‌شناسی قانونی (Simple Bot) برای ارزهای روند‌دار
  - Bounce Scalper برای ارزهای نوسانی
  - انتخاب per-asset با Smart Dispatcher
"""

from app.domain.entities.candle import Candle
from app.services.bots.base import BaseBot, BotInfo, BotStatus
from app.services.bots.mean_revert.config import MeanRevertConfig


class MeanRevertBot(BaseBot):
    """
    کف‌زن — خرید در کف، فروش در سود کوچک.

    ویژگی‌ها:
      - Per-asset strategy (Dispatcher)
      - Multi-timeframe support
      - Paper and Live capable
      - Per-asset thresholds
    """

    def __init__(self, config: MeanRevertConfig | None = None):
        self.config = config or MeanRevertConfig()
        self._status = BotStatus.IDLE

    @property
    def info(self) -> BotInfo:
        return BotInfo(
            slug="mean_revert",
            name="کف‌زن",
            name_en="Mean Revert Bot",
            version="0.1.0",
            description="خرید در کف و فروش در سود کوچک با استراتژی per-asset",
            tags=["mean_reversion", "scalping", "bottom_hunting"],
            capabilities=["paper", "live", "backtest"],
        )

    @property
    def status(self) -> BotStatus:
        return self._status

    async def start(self, exchange) -> dict:
        from app.services.paper_trader_v2 import paper_trader_v2

        result = await paper_trader_v2.start(exchange)
        self._status = BotStatus.RUNNING
        return result

    async def stop(self) -> dict:
        from app.services.paper_trader_v2 import paper_trader_v2

        result = await paper_trader_v2.stop()
        self._status = BotStatus.STOPPED
        return result

    def reset(self) -> dict:
        from app.services.paper_trader_v2 import paper_trader_v2

        result = paper_trader_v2.reset()
        self._status = BotStatus.IDLE
        return result

    def get_status(self) -> dict:
        from app.services.paper_trader_v2 import paper_trader_v2

        return paper_trader_v2.get_status()

    def make_decision(self, symbol: str, candles: list[Candle]) -> dict | None:
        """تصمیم ورود برای یک نماد."""
        from app.services.smart_dispatcher import dispatcher

        return dispatcher.make_decision(symbol, candles)
