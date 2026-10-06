"""Grid Bot — شبکه‌ای."""

import time
from dataclasses import dataclass, field

from app.domain.entities.candle import Candle
from app.services.bots.base import BaseBot, BotInfo, BotStatus
from app.services.bots.grid_bot.config import GridBotConfig
from app.services.bots.grid_bot.strategy import should_start_grid


@dataclass
class GridBotState:
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


class GridBot(BaseBot):
    """شبکه‌ای — پله‌ای خرید/فروش در محدوده."""

    def __init__(self, config: GridBotConfig | None = None):
        self.config = config or GridBotConfig()
        self.state = GridBotState()
        self._status = BotStatus.IDLE

    @property
    def info(self) -> BotInfo:
        return BotInfo(
            slug="grid_bot",
            name="شبکه‌ای",
            name_en="Grid Bot",
            version="0.1.0",
            description="پله‌ای خرید و فروش در محدوده‌ی قیمت، بدون پیش‌بینی جهت",
            tags=["grid", "range_trading", "passive", "scalping"],
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
        return {"status": "started", "bot": "grid_bot"}

    async def stop(self) -> dict:
        self._status = BotStatus.STOPPED
        self.state.is_running = False
        return {"status": "stopped"}

    def reset(self) -> dict:
        self.state = GridBotState()
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
            "active_symbols": ["BTCTMN", "ETHTMN", "XRPTMN", "SOLTMN"],
            "config": {
                "timeframe": self.config.timeframe,
                "n_buy_levels": self.config.n_buy_levels,
                "n_sell_levels": self.config.n_sell_levels,
                "grid_spacing_atr": self.config.grid_spacing_atr,
                "cash_per_level_pct": self.config.cash_per_level_pct,
                "adx_max": self.config.adx_max,
            },
        }

    def make_decision(self, symbol: str, candles: list[Candle]) -> dict | None:
        """تصمیم شروع گرید."""
        signal = should_start_grid(
            candles,
            symbol,
            self.state.capital,
            self.config,
        )
        if not signal.should_start or signal.plan is None:
            return None

        return {
            "should_trade": True,
            "action": "grid",
            "entry": signal.plan.center_price,
            "tp": 0,
            "sl": 0,
            "reason": signal.reason,
            "strategy": "grid_bot",
            "adx": signal.adx,
            "n_levels": len(signal.plan.levels),
        }
