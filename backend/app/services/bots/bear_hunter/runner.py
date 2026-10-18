import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from app.domain.ports.margin_exchange import MarginExchangePort
from .config import BearHunterConfig
from .state import BearHunterState, StateStore, reconcile
from .rules import calculate_position_size, calculate_short_levels
from .pre_flight import pre_flight_check
from .executor import execute_short_entry

logger = logging.getLogger(__name__)

@dataclass
class Signal:
    market: str
    size_tmn: Decimal
    entry_price: Decimal
    stop_loss: Decimal
    take_profit: Decimal
    sl_pct: Decimal
    tp_pct: Decimal
    current_price: Decimal
    age_seconds: int = 0
    is_paper: bool = True

class BearHunterRunner:
    def __init__(
        self,
        config: BearHunterConfig,
        state_store: StateStore,
        adapter: MarginExchangePort,
        tick_interval_sec: int = 300  # 5 minutes (changed from 60s)
    ):
        self.config = config
        self.store = state_store
        self.adapter = adapter
        self.tick_interval = tick_interval_sec
        self.state = self.store.load()
        self._running = False
        self._lock = asyncio.Lock()  # Guard 1: Overlap prevention
        self._consecutive_errors = 0

    async def start(self):
        self._running = True
        logger.info("Starting BearHunterRunner...")

        await self._reconcile()

        try:
            while self._running:
                try:
                    # Guard 2: Timeout protection (max 60s per tick)
                    await asyncio.wait_for(self._safe_tick(), timeout=60.0)
                    self._consecutive_errors = 0  # reset on success
                except asyncio.TimeoutError:
                    logger.error("Tick timed out after 60s.")
                    self._consecutive_errors += 1
                except Exception as e:
                    logger.error(f"Tick error: {e}", exc_info=True)
                    self._consecutive_errors += 1

                # Guard 3: Consecutive errors -> Kill Switch
                if self._consecutive_errors >= 3:
                    logger.critical("3 consecutive errors. Triggering kill switch.")
                    self.state.mark_kill_switch("3_consecutive_runner_errors", source="auto")
                    self.store.save(self.state)
                    self._running = False
                    break

                await asyncio.sleep(self.tick_interval)
        except KeyboardInterrupt:
            # Guard 4: Graceful shutdown
            logger.info("KeyboardInterrupt received. Saving state and exiting.")
        finally:
            self.stop()

    def stop(self):
        logger.info("Stopping BearHunterRunner...")
        self._running = False
        self.store.save(self.state)

    async def _safe_tick(self):
        """Wrap tick in a lock to prevent overlapping executions."""
        if self._lock.locked():
            logger.warning("Previous tick still running. Skipping this cycle.")
            return
        async with self._lock:
            await self.tick()

    async def tick(self):
        if not self.state.initialized:
            logger.warning("State not initialized. Skipping tick.")
            return

        if self.state.is_killed:
            logger.warning(f"Kill switch active: {self.state.kill_switch_reason}")
            return

        signal = self._generate_mock_signal()
        if signal:
            await self._process_signal(signal)
            self.store.save(self.state)

    async def _reconcile(self):
        if not self.state.initialized:
            return
        warnings = await reconcile(self.state, self.adapter)
        for w in warnings:
            logger.warning(f"Reconcile: {w}")
        self.store.save(self.state)

    async def _process_signal(self, signal: Signal):
        pre_flight = await pre_flight_check(
            signal=signal,
            state=self.state,
            config=self.config,
            adapter=self.adapter
        )

        if pre_flight.approved:
            pos = await execute_short_entry(
                signal=signal,
                pre_flight=pre_flight,
                state=self.state,
                config=self.config,
                adapter=self.adapter
            )
            if pos:
                logger.info(f"Position opened: {pos.position_id}")
        else:
            logger.info(f"Signal rejected: {pre_flight.reason} (Phase {pre_flight.phase})")

    def _generate_mock_signal(self) -> Optional[Signal]:
        if len(self.state.open_positions) > 0:
            return None
            
        entry = Decimal("21562618329")
        levels = calculate_short_levels(entry, self.config)
        sizing = calculate_position_size(
            capital_tmn=Decimal(str(self.state.capital_tmn)),
            config=self.config,
            daily_remaining_tmn=Decimal("300000"),
            current_price=entry
        )

        if sizing.size_tmn <= 0:
            return None

        return Signal(
            market="BTCTMN",
            size_tmn=sizing.size_tmn,
            entry_price=entry,
            stop_loss=levels.stop_loss,
            take_profit=levels.take_profit,
            sl_pct=levels.sl_distance_pct,
            tp_pct=levels.tp_distance_pct,
            current_price=entry,
            is_paper=self.state.paper_mode
        )
