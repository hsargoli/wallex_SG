"""Scalp Master Bot — اسکالپ نزولی (Monitor Mode).

ویژگی‌ها:
  - چک دوره‌ای نمادها
  - شناسایی سیگنال ورود
  - بدون ترید (فقط نمایش)
"""

import asyncio
import time

from app.domain.entities.candle import Candle
from app.domain.entities.paper_position import PaperPosition
from app.services.bots.base import BaseBot, BotInfo, BotStatus
from app.services.bots.scalp_master.config import ScalpMasterConfig
from app.services.bots.scalp_master.state import ScalpState
from app.services.bots.scalp_master.store import ScalpStore
from app.services.bots.scalp_master.strategy import evaluate_entry


class ScalpMasterBot(BaseBot):
    """اسکالپ نزولی — Monitor Mode (فقط سیگنال)."""

    def __init__(self, config: ScalpMasterConfig | None = None):
        self.config = config or ScalpMasterConfig()
        self.store = ScalpStore()
        self._states: dict[str, ScalpState] = {}
        self._status = BotStatus.IDLE

    def _get_state(self, user_id: str) -> ScalpState:
        if user_id not in self._states:
            self._states[user_id] = self.store.load(user_id)
        return self._states[user_id]

    @property
    def state(self) -> ScalpState:
        """Backward-compat: default user's state."""
        return self._get_state("default")

    @property
    def info(self) -> BotInfo:
        return BotInfo(
            slug="scalp_master",
            name="اسکالپ‌مستر",
            name_en="Scalp Master Bot",
            version="0.1.0",
            description="خرید پس از سقوط و فروش با سود کم (اسکالپ نزولی)",
            tags=["scalping", "dip_buy", "mean_reversion"],
            capabilities=["monitor", "signal", "display", "paper"],
            tier="production",
        )

    @property
    def status(self) -> BotStatus:
        return self._status

    async def start(self, exchange, user_id: str = "default") -> dict:
        """شروع چک دوره‌ای."""
        state = self._get_state(user_id)
        if state.is_running:
            return {"status": "already_running"}

        self._status = BotStatus.RUNNING
        state.is_running = True
        state.started_at = int(time.time())
        self.store.save(user_id, state)

        # اولین چک
        await self._check_symbols(exchange, user_id=user_id)

        # loop
        state._task = asyncio.create_task(self._loop(exchange, user_id=user_id))

        return {
            "status": "started",
            "bot": "scalp_master",
            "symbols": self.config.symbols,
            "interval_sec": self.config.check_interval_sec,
        }

    async def stop(self, user_id: str = "default") -> dict:
        """توقف."""
        state = self._get_state(user_id)
        self._status = BotStatus.STOPPED
        state.is_running = False
        self.store.save(user_id, state)

        if state._task and not state._task.done():
            state._task.cancel()
            try:
                await state._task
            except asyncio.CancelledError:
                pass

        return {"status": "stopped"}

    def reset(self, user_id: str = "default") -> dict:
        """ریست."""
        self._states[user_id] = ScalpState()
        self.store.save(user_id, self._states[user_id])
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

    def get_status(self, user_id: str = "default") -> dict:
        """وضعیت کامل."""
        s = self._get_state(user_id)
        from dataclasses import asdict
        return {
            "is_running": s.is_running,
            "paper_mode": s.paper_mode,
            "capital": s.capital,
            "open_positions": [asdict(p) for p in s.open_positions],
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

    def diagnose(self, symbol: str, candles: list[Candle]) -> list[dict]:
        """نتیجه‌ی هر شرط ورود."""
        from app.services.bots.scalp_master.strategy import diagnose_entry
        return diagnose_entry(candles, self.config)

    # ─── Internals ───

    async def _loop(self, exchange, user_id: str = "default") -> None:
        """Loop چک دوره‌ای."""
        state = self._get_state(user_id)
        while state.is_running:
            try:
                await asyncio.sleep(self.config.check_interval_sec)
                if not state.is_running:
                    break
                await self._check_symbols(exchange, user_id=user_id)
            except asyncio.CancelledError:
                break
            except Exception:
                await asyncio.sleep(60)

    async def _check_symbols(self, exchange, user_id: str = "default") -> None:
        """چک همه نمادها."""
        from app.application.use_cases.get_candles import GetCandlesUseCase
        state = self._get_state(user_id)

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
                    self._log_signal(symbol, signal, user_id=user_id)
                    if state.paper_mode:  # P2c: paper entry
                        self._paper_entry(symbol, signal, user_id=user_id)
            except Exception:
                continue

        state.last_check_at = int(time.time())
        state.check_count += 1
        self.store.save(user_id, state)

    def _paper_entry(self, symbol: str, signal, user_id: str = "default") -> "PaperPosition | None":
        """Create + append a virtual PaperPosition (paper mode only, no exchange call)."""
        state = self._get_state(user_id)
        if not state.paper_mode:
            return None
        entry_price = float(signal.entry_price)
        if entry_price <= 0:
            return None  # fail-safe: invalid price
        alloc_tmn = state.capital * (self.config.position_size_pct / 100)
        quantity = alloc_tmn / entry_price  # TMN allocation → units
        pos = PaperPosition(
            symbol=symbol,
            side="BUY",
            entry_price=entry_price,
            quantity=quantity,
            tp=float(signal.take_profit),
            sl=float(signal.stop_loss),
            entry_time=int(time.time()),
            entry_idx=state.check_count,
            reason=signal.reason,
            bot_slug="scalp_master",
        )
        state.open_positions.append(pos)
        self.store.save(user_id, state)
        return pos

    def _log_signal(self, symbol: str, signal, user_id: str = "default") -> None:
        """ذخیره سیگنال."""
        state = self._get_state(user_id)
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
        state.recent_signals.insert(0, entry)
        if len(state.recent_signals) > self.config.max_signals:
            state.recent_signals = state.recent_signals[: self.config.max_signals]
        self.store.save(user_id, state)
