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

async def main() -> None:
    """Entrypoint. Usage: python -m app.services.bots.bear_hunter.runner [args]"""
    import argparse, os, sys
    import logging as _log
    import signal as _sig

    parser = argparse.ArgumentParser(description="Bear Hunter Runner")
    parser.add_argument("--user-id", default=None)
    parser.add_argument("--interval", type=int, default=300)
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    _log.basicConfig(
        level=_log.INFO if args.verbose else _log.WARNING,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    api_key = os.environ.get("WALLEX_VIEW_TOKEN", "").strip()
    if not api_key:
        print("ERROR: WALLEX_VIEW_TOKEN env required", file=sys.stderr)
        sys.exit(1)

    from app.infrastructure.exchange.wallex.margin_adapter import WallexMarginAdapter
    from app.services.bots.bear_hunter.paths import USERS_DIR

    adapter = WallexMarginAdapter(api_key=api_key)
    config = BearHunterConfig()

    if not USERS_DIR.exists():
        print(f"ERROR: {USERS_DIR} not found", file=sys.stderr)
        sys.exit(1)

    user_files = ([USERS_DIR / f"{args.user_id}.json"] if args.user_id
                  else sorted(USERS_DIR.glob("*.json")))
    if not user_files:
        print(f"ERROR: no *.json in {USERS_DIR}", file=sys.stderr)
        sys.exit(1)

    runners = []
    for uf in user_files:
        if not uf.exists():
            print(f"WARN: {uf.name} not found")
            continue
        store = StateStore(path=str(uf))
        st = store.load()
        if not st.initialized or not st.human_signal:
            print(f"WARN: {uf.name} not initialized or no signal")
            continue
        runners.append((uf.stem, BearHunterRunner(config, store, adapter, args.interval)))
        print(f"OK: {uf.stem} status={st.bot_status} paper={st.paper_mode}")

    if not runners:
        print("ERROR: no runnable bots", file=sys.stderr)
        sys.exit(1)

    if args.once:
        for name, runner in runners:
            bp, bt = len(runner.state.open_positions), runner.state.trades_today
            print(f">> tick {name}")
            try:
                await runner.tick()
                print(f"   OK: positions {bp}->{len(runner.state.open_positions)}, "
                      f"trades {bt}->{runner.state.trades_today}, "
                      f"status={runner.state.bot_status}")
            except Exception as e:
                import traceback
                print(f"FAIL {name}: {e}", file=sys.stderr)
                traceback.print_exc()
        return

    stop_event = asyncio.Event()
    def _stop(*_): stop_event.set()
    loop = asyncio.get_event_loop()
    for sig in (_sig.SIGINT, _sig.SIGTERM):
        try: loop.add_signal_handler(sig, _stop)
        except NotImplementedError: pass

    print(f"START {len(runners)} runner(s), interval={args.interval}s")
    tasks = [asyncio.create_task(rr.start(), name=name) for name, rr in runners]
    await stop_event.wait()
    print("STOP requested")
    for _, rr in runners: rr.stop()
    await asyncio.gather(*tasks, return_exceptions=True)
    print("DONE")


if __name__ == "__main__":
    asyncio.run(main())

