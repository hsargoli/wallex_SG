"""CandlePrefetcher: warm the candle cache for top-N symbols.

Per CTO 2026-10-24:
- top_n=10, interval_sec=300 (~11% wallex duty cycle)
- Uses Semaphore(5) internally to avoid wallex pressure
- Errors in one cycle do NOT crash the loop (log and continue)
- cache is the shared singleton from app.infrastructure.cache.candles
"""
from __future__ import annotations

import asyncio
import structlog

from app.application.use_cases.get_candles import GetCandlesUseCase
from app.domain.ports.exchange import ExchangePort

logger = structlog.get_logger(__name__)

TIMEFRAMES: tuple[str, ...] = ("1h", "1D")
FETCH_LIMIT = 100        # 1h — matches frontend (queries.ts limit=100)
FETCH_LIMIT_1D = 31      # 1D — minimum for change_1m (needs daily[-31])
SEMAPHORE_LIMIT = 5


class CandlePrefetcher:
    """Background task that warms candle cache for top-volume symbols.

    Design notes:
    - One cycle: get_markets -> sort by daily_quote_volume desc -> top N
      -> for each (symbol, timeframe): GetCandlesUseCase.execute (caches)
    - Semaphore(5) bounds concurrent wallex calls (same limit as signals
      endpoint, per SERVER_INVENTORY + f0e2a3f rollback).
    - Errors per symbol/timeframe are logged and swallowed — loop continues.
    """

    def __init__(
        self,
        exchange: ExchangePort,
        top_n: int = 10,
        interval_sec: int = 300,
    ) -> None:
        if top_n < 1:
            raise ValueError("top_n must be >= 1")
        if interval_sec < 1:
            raise ValueError("interval_sec must be >= 1")
        self._exchange = exchange
        self._use_case = GetCandlesUseCase(exchange=exchange)
        self._top_n = top_n
        self._interval_sec = interval_sec
        self._sem = asyncio.Semaphore(SEMAPHORE_LIMIT)
        self._stopped = asyncio.Event()

    async def run(self) -> None:
        """Main loop: one cycle, sleep, repeat. Cancel to stop."""
        logger.info(
            "prefetcher.start",
            extra={"top_n": self._top_n, "interval_sec": self._interval_sec},
        )
        try:
            while not self._stopped.is_set():
                try:
                    await self._refresh_top()
                except asyncio.CancelledError:
                    raise
                except Exception as exc:
                    logger.warning("prefetcher.cycle_error", extra={"err": str(exc)})
                try:
                    await asyncio.wait_for(
                        self._stopped.wait(), timeout=self._interval_sec
                    )
                except asyncio.TimeoutError:
                    pass
        finally:
            logger.info("prefetcher.stop")

    def stop(self) -> None:
        """Signal the loop to exit on next iteration."""
        self._stopped.set()

    async def _refresh_top(self) -> None:
        """One cycle: fetch top-N symbols x TIMEFRAMES, populate cache."""
        try:
            markets = await self._exchange.get_markets()
        except Exception as exc:
            logger.warning("prefetcher.get_markets_error", extra={"err": str(exc)})
            return

        ranked = sorted(
            markets,
            key=lambda m: float(
                getattr(getattr(m, "stats", None), "daily_quote_volume", 0) or 0
            ),
            reverse=True,
        )
        top = ranked[: self._top_n]
        if not top:
            return

        async def _one(symbol: str, timeframe: str) -> None:
            async with self._sem:
                limit = FETCH_LIMIT_1D if timeframe == "1D" else FETCH_LIMIT
                # Retry once on failure (wallex can be flaky; 2026-10-25)
                last_err: Exception | None = None
                # 1D: timeout 10s (wallex slow/flaky; CTO 2026-10-25)
                # 1h: full timeout (fast, cache warm is critical)
                call_timeout = 10.0 if timeframe == "1D" else None
                for attempt in (1, 2):
                    try:
                        coro = self._use_case.execute(
                            symbol=symbol, timeframe=timeframe, limit=limit
                        )
                        if call_timeout is not None:
                            await asyncio.wait_for(coro, timeout=call_timeout)
                        else:
                            await coro
                        return
                    except asyncio.CancelledError:
                        raise
                    except Exception as exc:
                        last_err = exc
                        if attempt == 1:
                            await asyncio.sleep(2)  # brief backoff
                logger.warning(
                    "prefetcher.symbol_error",
                    extra={
                        "symbol": symbol,
                        "timeframe": timeframe,
                        "err": str(last_err),
                    },
                )

        # Sequential per timeframe: 1h first (fast, cache-warm), then 1D
        # (slower). Parallel 1h+1D starves 1h via Semaphore(5) when 1D is slow,
        # causing 1h timeouts and empty cache (observed 2026-10-25).
        for tf in TIMEFRAMES:
            tasks = [_one(str(m.symbol), tf) for m in top]
            await asyncio.gather(*tasks)

        total_calls = len(top) * len(TIMEFRAMES)
        logger.info(
            "prefetcher.cycle_done",
            extra={"symbols": len(top), "calls": total_calls},
        )
