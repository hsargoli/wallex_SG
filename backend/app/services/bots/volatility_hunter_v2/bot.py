"""Volatility Hunter v2 — نسخه بهبودیافته.

هنوز live engine نداره. فعلاً:
  - از registry قابل کشف است
  - از simulate_engine قابل استفاده است
  - از UI قابل مشاهده است
"""

from dataclasses import dataclass, field
import time

from app.domain.entities.candle import Candle
from app.services.bots.base import BaseBot, BotInfo, BotStatus
from app.services.bots.volatility_hunter_v2.config import VolatilityHunterV2Config
from app.services.bots.volatility_hunter_v2.strategy import (
    evaluate_entry_v2,
    evaluate_exit_v2,
)


@dataclass
class HunterV2State:
    """state ربات."""

    is_running: bool = False
    initial_capital: float = 300_000.0
    capital: float = 300_000.0
    peak_capital: float = 300_000.0
    max_drawdown_pct: float = 0.0
    total_trades: int = 0
    wins: int = 0
    losses: int = 0
    started_at: int = 0
    open_positions: list[dict] = field(default_factory=list)
    recent_trades: list[dict] = field(default_factory=list)


class VolatilityHunterV2Bot(BaseBot):
    """نوسان‌گیر v2 — با فیلترهای بهبودیافته."""

    def __init__(self, config: VolatilityHunterV2Config | None = None):
        self.config = config or VolatilityHunterV2Config()
        self.state = HunterV2State()
        self._status = BotStatus.IDLE

    @property
    def info(self) -> BotInfo:
        return BotInfo(
            slug="volatility_hunter_v2",
            name="نوسان‌گیر v2",
            name_en="Volatility Hunter v2",
            version="0.2.0",
            description=(
                "نسخه بهبودیافته‌ی نوسان‌گیر — با فیلتر ADX، "
                "تأیید RSI، فیلتر حجم، و SL/TP بر مبنای ATR"
            ),
            tags=["volatility", "range_trading", "mean_reversion", "atr", "adx"],
            capabilities=["backtest", "paper", "live"],
        )

    @property
    def status(self) -> BotStatus:
        return self._status

    async def start(self, exchange) -> dict:
        self._status = BotStatus.RUNNING
        self.state.is_running = True
        if self.state.started_at == 0:
            self.state.started_at = int(time.time())
        return {"status": "started", "bot": "volatility_hunter_v2"}

    async def stop(self) -> dict:
        self._status = BotStatus.STOPPED
        self.state.is_running = False
        return {"status": "stopped"}

    def reset(self) -> dict:
        self.state = HunterV2State()
        self._status = BotStatus.IDLE
        return {"status": "reset"}

    def get_status(self) -> dict:
        s = self.state
        wr = (s.wins / s.total_trades * 100) if s.total_trades > 0 else 0
        ret = (s.capital - s.initial_capital) / s.initial_capital * 100
        runtime_min = (int(time.time()) - s.started_at) // 60 if s.started_at else 0

        return {
            "is_running": s.is_running,
            "started_at": s.started_at,
            "runtime_minutes": runtime_min,
            "initial_capital": s.initial_capital,
            "current_capital": round(s.capital, 1),
            "total_return_pct": round(ret, 2),
            "profit_tmn": round(s.capital - s.initial_capital, 1),
            "max_drawdown_pct": round(s.max_drawdown_pct, 2),
            "total_trades": s.total_trades,
            "wins": s.wins,
            "losses": s.losses,
            "win_rate": round(wr, 2),
            "open_positions": s.open_positions,
            "recent_trades": s.recent_trades[:20],
            "active_symbols": [],
            "config": {
                "timeframe": self.config.timeframe,
                "max_adx": self.config.max_adx,
                "min_range_pct": self.config.min_range_pct,
                "max_range_pct": self.config.max_range_pct,
                "buy_zone_pct": self.config.buy_zone_pct,
                "max_rsi": self.config.max_rsi,
                "sl_atr_mult": self.config.sl_atr_mult,
                "tp_atr_mult": self.config.tp_atr_mult,
                "position_size_pct": self.config.position_size_pct,
            },
        }

    def make_decision(self, symbol: str, candles: list[Candle]) -> dict | None:
        """تصمیم ورود — هم‌سازگار با simulator_engine و bot_simulator."""
        signal = evaluate_entry_v2(candles, self.config)
        if signal is None or not signal.should_trade:
            return None

        return {
            "should_trade": True,
            "action": signal.action,
            "entry": signal.entry_price,
            "tp": signal.take_profit,
            "sl": signal.stop_loss,
            "reason": signal.reason,
            "strategy": "volatility_hunter_v2",
            "confidence": signal.confidence,
        }
