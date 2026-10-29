"""SarvRouterScheduler — tick SarvRouter every N minutes using exchange data."""
from __future__ import annotations

import structlog
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.application.use_cases.get_candles import GetCandlesUseCase
from app.domain.ports.exchange import ExchangePort
from app.services.bots.sarv_router.audit import AuditTrail
from app.services.bots.sarv_router.bot import SarvRouter
from app.services.bots.sarv_router.config import SarvRouterConfig
from app.services.bots.sarv_router.store import SarvStore

log = structlog.get_logger("sarv_router.scheduler")


class SarvRouterScheduler:
    """Tick SarvRouter every N minutes. Uses exchange data (not CSV)."""

    def __init__(
        self,
        exchange: ExchangePort,
        interval_minutes: int = 30,
        user_id: str = "production-default",
        symbol: str = "BTCTMN",
        timeframe: str = "1h",
        candle_limit: int = 300,
    ):
        self._exchange = exchange
        self._interval = interval_minutes
        self._user_id = user_id
        self._symbol = symbol
        self._timeframe = timeframe
        self._candle_limit = candle_limit
        self._scheduler: AsyncIOScheduler | None = None
        self._last_result: dict | None = None
        self._last_error: str | None = None

    def start(self) -> None:
        if self._scheduler is not None:
            log.warning("sarv_router.scheduler_already_started")
            return
        self._scheduler = AsyncIOScheduler()
        self._scheduler.add_job(
            self._job, "interval", minutes=self._interval,
            id="sarv_router_tick", max_instances=1, coalesce=True,
        )
        self._scheduler.start()
        log.info("sarv_router.scheduler_started", interval_minutes=self._interval)

    def stop(self) -> None:
        if self._scheduler is not None:
            self._scheduler.shutdown(wait=False)
            self._scheduler = None
            log.info("sarv_router.scheduler_stopped")

    async def _job(self) -> None:
        try:
            uc = GetCandlesUseCase(exchange=self._exchange)
            candles = await uc.execute(
                symbol=self._symbol,
                timeframe=self._timeframe,
                limit=self._candle_limit,
            )
            if not candles:
                self._last_error = "no candles loaded"
                log.error("sarv_router.no_candles", symbol=self._symbol)
                return

            router = SarvRouter(
                config=SarvRouterConfig(),
                start_bot=lambda s: None,
                stop_bot=lambda s: None,
                stop_all=lambda: None,
                store=SarvStore(),
                audit=AuditTrail(),
            )
            result = router.tick(self._user_id, candles, now_idx=len(candles) - 1)
            self._last_result = result
            self._last_error = None
            log.info(
                "sarv_router.tick_done",
                action=result.get("action"),
                regime=result.get("regime"),
                active_bots=result.get("active_bots"),
                candles=len(candles),
            )
        except Exception as exc:
            self._last_error = str(exc)
            log.error("sarv_router.tick_failed", error=str(exc))

    @property
    def last_result(self) -> dict | None:
        return self._last_result

    @property
    def last_error(self) -> str | None:
        return self._last_error

    @property
    def running(self) -> bool:
        return self._scheduler is not None and self._scheduler.running
