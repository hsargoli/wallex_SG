"""NooaahScheduler — اجرای خودکار NooaahRunner هر ۱ ساعت.

تو FastAPI lifespan start می‌شه.
Single-worker only (طبق ADR-0010).
"""

from __future__ import annotations

import asyncio
from typing import Any

import structlog
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.domain.ports.exchange import ExchangePort
from app.services.bots.nooaah.config import NooaahConfig
from app.services.bots.nooaah.runner import NooaahRunner
from app.services.bots.nooaah.state import NooaahState

log = structlog.get_logger("nooaah.scheduler")


class NooaahScheduler:
    """Scheduler برای اجرای NooaahRunner به‌صورت دوره‌ای."""

    def __init__(
        self,
        exchange: ExchangePort,
        interval_minutes: int = 60,
    ) -> None:
        self._exchange = exchange
        self._interval = interval_minutes
        self._scheduler: AsyncIOScheduler | None = None
        self._last_result: dict[str, Any] | None = None
        self._last_error: str | None = None

    def start(self) -> None:
        if self._scheduler is not None:
            log.warning("nooaah.scheduler_already_started")
            return

        self._scheduler = AsyncIOScheduler()
        self._scheduler.add_job(
            self._job,
            "interval",
            minutes=self._interval,
            id="nooaah_cycle",
            max_instances=1,  # هیچ‌وقت دو cycle هم‌زمان
            coalesce=True,  # اگه عقب افتاد، یک بار جبران
        )
        self._scheduler.start()
        log.info(
            "nooaah.scheduler_started",
            interval_minutes=self._interval,
        )

    def stop(self) -> None:
        if self._scheduler is not None:
            self._scheduler.shutdown(wait=False)
            self._scheduler = None
            log.info("nooaah.scheduler_stopped")

    async def _job(self) -> None:
        """هر بار اجرای runner."""
        try:
            # از runtime_config موجود در state بخون (ADR-0012)
            state = NooaahState.load()
            rc = state.get_runtime_config()

            cfg = NooaahConfig(
                top_n=int(rc.get("top_n", 5)),
                min_confidence=int(rc.get("min_confidence", 85)),
                confirmation_candles=int(rc.get("confirmation_candles", 2)),
                tp_atr_mult=float(rc.get("tp_atr_mult", 3.0)),
                sl_atr_mult=float(rc.get("sl_atr_mult", 1.5)),
                volume_z_min=float(rc.get("volume_z_min", -0.5)),
                max_concurrent_positions=int(rc.get("max_concurrent_positions", 1)),
            )
            runner = NooaahRunner(exchange=self._exchange, config=cfg)
            result = await runner.run_cycle()
            self._last_result = result
            self._last_error = None
            log.info(
                "nooaah.cycle_done",
                status=result.get("status"),
                open=result.get("open_positions"),
                daily_pnl=result.get("daily_pnl_pct"),
            )
        except Exception as exc:
            self._last_error = str(exc)
            log.error("nooaah.cycle_failed", error=str(exc))

    @property
    def last_result(self) -> dict[str, Any] | None:
        return self._last_result

    @property
    def last_error(self) -> str | None:
        return self._last_error

    @property
    def running(self) -> bool:
        return self._scheduler is not None and self._scheduler.running


# ---------- Singleton ----------
_scheduler_instance: NooaahScheduler | None = None


def get_scheduler() -> NooaahScheduler | None:
    return _scheduler_instance


def set_scheduler(s: NooaahScheduler) -> None:
    global _scheduler_instance
    _scheduler_instance = s
