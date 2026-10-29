"""SarvRouterScheduler — tick SarvRouter every N minutes (like nooaah)."""
from __future__ import annotations

import csv
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

import structlog
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.domain.entities.candle import Candle
from app.services.bots.sarv_router.audit import AuditTrail
from app.services.bots.sarv_router.bot import SarvRouter
from app.services.bots.sarv_router.config import SarvRouterConfig
from app.services.bots.sarv_router.store import SarvStore

log = structlog.get_logger("sarv_router.scheduler")

_BACKEND = Path(__file__).resolve().parent.parent.parent.parent.parent
_CSV = _BACKEND / "data" / "candles" / "historical" / "BTCUSDT_1h.csv"


class SarvRouterScheduler:
    """Tick SarvRouter every N minutes. Single-worker only."""

    def __init__(self, interval_minutes: int = 30, user_id: str = "production-default"):
        self._interval = interval_minutes
        self._user_id = user_id
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
            candles = _load_recent(300)
            if not candles:
                self._last_error = "no candles loaded"
                log.error("sarv_router.no_candles")
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


def _load_recent(n: int = 300) -> list[Candle]:
    if not _CSV.exists():
        return []
    out = []
    with open(_CSV) as f:
        for row in csv.DictReader(f):
            ts = int(row["open_time"])
            if ts > 10_000_000_000:
                ts //= 1000
            out.append(Candle(
                time=ts, open=Decimal(row["open"]), high=Decimal(row["high"]),
                low=Decimal(row["low"]), close=Decimal(row["close"]),
                volume=Decimal(row["volume"]),
            ))
    return out[-n:]
