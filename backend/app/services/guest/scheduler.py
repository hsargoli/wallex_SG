"""Guest Scheduler — loop مشترک برای همه‌ی guest engineها.

یه loop، هر N ثانیه، همه‌ی engineهای در حال اجرا رو check می‌کنه.
(به‌جای per-guest task که منابع رو سرریز می‌کنه)

منابع:
- docs/design/GUEST_MODE.md (v2.1) — بخش ۵
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Callable

import structlog

if TYPE_CHECKING:
    from app.infrastructure.paper_trading.engine import PaperEngine

log = structlog.get_logger("guest.scheduler")


class GuestScheduler:
    """Scheduler مشترک برای همه‌ی Guest Paper Engineها."""

    def __init__(self, interval_sec: int = 180, cleanup_interval_sec: int = 24 * 3600):
        self.interval_sec = interval_sec
        self.cleanup_interval_sec = cleanup_interval_sec
        self._task: asyncio.Task | None = None
        self._engines_provider: Callable[[], dict[str, "PaperEngine"]] | None = None
        self._user_engines_provider: Callable[[], dict[str, "PaperEngine"]] | None = None
        self._running = False
        self._last_cleanup_ts: float = 0.0

    def set_engines_provider(
        self, provider: Callable[[], dict[str, "PaperEngine"]]
    ) -> None:
        """تابعی که dict engineهای guest رو برمی‌گردونه."""
        self._engines_provider = provider

    def set_user_engines_provider(
        self, provider: Callable[[], dict[str, "PaperEngine"]]
    ) -> None:
        """تابعی که dict engineهای user رو برمی‌گردونه.

        جدا از guests — هر دو با هم توی _tick() check می‌شن.
        """
        self._user_engines_provider = provider

    def start(self) -> None:
        """شروع loop."""
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._loop())
        log.info("guest.scheduler_started", interval_sec=self.interval_sec)

    async def stop(self) -> None:
        """توقف loop."""
        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        log.info("guest.scheduler_stopped")

    async def _loop(self) -> None:
        """Loop اصلی."""
        while self._running:
            try:
                await asyncio.sleep(self.interval_sec)
                if not self._running:
                    break
                await self._tick()
            except asyncio.CancelledError:
                break
            except Exception as e:
                log.error("guest.scheduler_error", error=str(e))
                await asyncio.sleep(30)
                continue
            await self._maybe_cleanup()

    async def _tick(self) -> None:
        """یه چرخه: همه‌ی engineهای در حال اجرا رو check کن.

        هم guestها هم userها — با هم.
        """
        active = 0

        # guestها
        if self._engines_provider is not None:
            guests = self._engines_provider()
            for token, engine in guests.items():
                if not engine.state.is_running:
                    continue
                active += 1
                try:
                    await engine._check()
                except Exception as e:
                    log.error(
                        "guest.check_failed",
                        token=token[:8] + "...",
                        error=str(e),
                    )

        # userها
        if self._user_engines_provider is not None:
            users = self._user_engines_provider()
            for user_id, engine in users.items():
                if not engine.state.is_running:
                    continue
                active += 1
                try:
                    await engine._check()
                except Exception as e:
                    log.error(
                        "user.check_failed",
                        user_id=str(user_id)[:8] + "...",
                        error=str(e),
                    )

        if active:
            log.info("paper.scheduler_tick", active=active)

    async def _maybe_cleanup(self) -> None:
        """Run cleanup_stale_guests if enough time has passed."""
        import time
        now = time.time()
        if now - self._last_cleanup_ts < self.cleanup_interval_sec:
            return
        try:
            from app.services.guest.storage import cleanup_stale_guests
            removed = cleanup_stale_guests()
            self._last_cleanup_ts = now
            if removed:
                log.info("guest.cleanup", removed=removed, interval_sec=self.cleanup_interval_sec)
            else:
                log.debug("guest.cleanup_noop")
        except Exception as e:
            log.error("guest.cleanup_failed", error=str(e))

