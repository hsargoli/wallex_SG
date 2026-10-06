"""Scalp Master Bot — اسکالپ نزولی (Monitor Mode).

ویژگی‌ها:
  - چک دوره‌ای نمادها
  - شناسایی سیگنال ورود
  - بدون ترید (فقط نمایش)
"""

import asyncio
import time
from dataclasses import dataclass, field

from app.domain.entities.candle import Candle
from app.services.bots.base import BaseBot, BotInfo, BotStatus
from app.services.bots.scalp_master.config import ScalpMasterConfig
from app.services.bots.scalp_master.strategy import evaluate_entry


@dataclass
class ScalpState:
    """State اسکالپ‌مستر."""

    is_running: bool = False
    started_at: int = 0
    last_check_at: int = 0
    check_count: int = 0
    recent_signals: list[dict] = field(default_factory=list)
    _task: asyncio.Task | None = None


class ScalpMasterBot(BaseBot):
    """اسکالپ نزولی — Monitor Mode (فقط سیگنال)."""

    def __init__(self, config: ScalpMasterConfig | None = None):
        self.config = config or ScalpMasterConfig()
        self.state = ScalpState()
        self._status = BotStatus.IDLE

    @property
    def info(self) -> BotInfo:
        return BotInfo(
            slug="scalp_master",
            name="اسکالپ‌مستر",
            name_en="Scalp Master Bot",
            version="0.1.0",
            description="خرید پس از سقوط و فروش با سود کم (اسکالپ نزولی)",
            tags=["scalping", "dip_buy", "mean_reversion"],
            capabilities=["monitor", "signal", "display"],
        )

    @property
    def status(self) -> BotStatus:
        return self._status

    async def start(self, exchange) -> dict:
        """شروع چک دوره‌ای."""
        if self.state.is_running:
            return {"status": "already_running"}

        self._status = BotStatus.RUNNING
        self.state.is_running = True
        self.state.started_at = int(time.time())

        # اولین چک
        await self._check_symbols(exchange)

        # loop
        self.state._task = asyncio.create_task(self._loop(exchange))

        return {
            "status": "started",
            "bot": "scalp_master",
            "symbols": self.config.symbols,
            "interval_sec": self.config.check_interval_sec,
        }

    async def stop(self) -> dict:
        """توقف."""
        self._status = BotStatus.STOPPED
        self.state.is_running = False

        if self.state._task and not self.state._task.done():
            self.state._task.cancel()
            try:
                await self.state._task
            except asyncio.CancelledError:
                pass

        return {"status": "stopped"}

    def reset(self) -> dict:
        """ریست."""
        self.state = ScalpState()
        self._status = BotStatus.IDLE
        return {"status": "reset"}

    def set_symbols(self, symbols: list[str]) -> dict:
        """تعیین نمادها (حداکثر ۲ تا)."""
        if not symbols:
            return {"status": "error", "message": "حداقل یک نماد لازم است"}
        if len(symbols) > 2:
            return {"status": "error", "message": "حداکثر ۲ نماد"}
        self.config.symbols = symbols
        return {"status": "ok", "symbols": symbols}

    def get_status(self) -> dict:
        """وضعیت کامل."""
        s = self.state
        return {
            "is_running": s.is_running,
            "started_at": s.started_at,
            "last_check_at": s.last_check_at,
            "check_count": s.check_count,
            "signals_count": len(s.recent_signals),
            "signals": s.recent_signals[:20],
            "symbols": self.config.symbols,
            "config": {
                "timeframe": self.config.timeframe,
                "drop_threshold_pct": self.config.drop_threshold_pct,
                "sl_atr_mult": self.config.sl_atr_mult,
                "tp_atr_mult": self.config.tp_atr_mult,
                "check_interval_sec": self.config.check_interval_sec,
            },
        }

    def make_decision(self, symbol: str, candles: list[Candle]) -> dict | None:
        """تصمیم ورود (backtest)."""
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

    # ─── Internals ───

    async def _loop(self, exchange) -> None:
        """Loop چک دوره‌ای."""
        while self.state.is_running:
            try:
                await asyncio.sleep(self.config.check_interval_sec)
                if not self.state.is_running:
                    break
                await self._check_symbols(exchange)
            except asyncio.CancelledError:
                break
            except Exception:
                await asyncio.sleep(60)

    async def _check_symbols(self, exchange) -> None:
        """چک همه نمادها."""
        from app.application.use_cases.get_candles import GetCandlesUseCase

        for symbol in self.config.symbols:
            try:
                uc = GetCandlesUseCase(exchange=exchange)
                candles = await uc.execute(
                    symbol=symbol,
                    timeframe=self.config.timeframe,
                    limit=200,
                )

                if not candles or len(candles) < self.config.warmup_candles:
                    continue

                signal = evaluate_entry(candles, self.config)

                if signal and signal.should_trade:
                    self._log_signal(symbol, signal)
            except Exception:
                continue

        self.state.last_check_at = int(time.time())
        self.state.check_count += 1

    def _log_signal(self, symbol: str, signal) -> None:
        """ذخیره سیگنال."""
        entry = {
            "symbol": symbol,
            "action": signal.action,
            "entry": signal.entry_price,
            "tp": signal.take_profit,
            "sl": signal.stop_loss,
            "reason": signal.reason,
            "drop_pct": signal.drop_pct,
            "rsi": signal.rsi,
            "time": int(time.time()),
        }
        self.state.recent_signals.insert(0, entry)
        if len(self.state.recent_signals) > self.config.max_signals:
            self.state.recent_signals = self.state.recent_signals[: self.config.max_signals]
