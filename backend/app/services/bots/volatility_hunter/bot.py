"""Volatility Hunter Bot — نوسان‌گیر."""

import time
from dataclasses import dataclass, field

from app.domain.entities.candle import Candle
from app.services.bots.base import BaseBot, BotInfo, BotStatus
from app.services.bots.volatility_hunter.config import VolatilityHunterConfig
from app.services.bots.volatility_hunter.strategy import (
    evaluate_entry,
)


@dataclass
class HunterState:
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


class VolatilityHunterBot(BaseBot):
    """نوسان‌گیر — شکار نوسانات در محدوده."""

    def __init__(self, config: VolatilityHunterConfig | None = None):
        self.config = config or VolatilityHunterConfig()
        self.state = HunterState()
        self._status = BotStatus.IDLE

    @property
    def info(self) -> BotInfo:
        return BotInfo(
            slug="volatility_hunter",
            name="نوسان‌گیر",
            name_en="Volatility Hunter Bot",
            version="0.1.0",
            description="تشخیص نوسان‌های شدید، خرید در کف range و فروش در سقف با خروج سریع",
            tags=["volatility", "range_trading", "mean_reversion", "scalping"],
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
        return {"status": "started", "bot": "volatility_hunter"}

    async def stop(self) -> dict:
        self._status = BotStatus.STOPPED
        self.state.is_running = False
        return {"status": "stopped"}

    def reset(self) -> dict:
        self.state = HunterState()
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
            "active_symbols": ["ZECTMN", "DASHTMN", "GRAMTMN", "XRPTMN"],
            "config": {
                "timeframe": self.config.timeframe,
                "min_atr_pct": self.config.min_atr_pct,
                "min_range_pct": self.config.min_range_pct,
                "max_range_pct": self.config.max_range_pct,
                "buy_zone_pct": self.config.buy_zone_pct,
                "position_size_pct": self.config.position_size_pct,
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
            "strategy": "volatility_hunter",
            "confidence": signal.confidence,
        }
