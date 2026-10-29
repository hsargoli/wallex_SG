"""
Presence Tracker — 3-level rule based on user inactivity.

Levels (per ADR 0020 §1):
  - NORMAL  (<48h)  : no action
  - DAY2    (>=48h) : block new entries
  - DAY3    (>=72h) : close PROFITABLE positions only
  - DAY4    (>=96h) : close ALL positions + idle

Pure logic — no I/O. Runner calls these methods each tick.

Boundary semantics: >= (inclusive). Exactly 48h → DAY2.
Alert rate-limit: 6h cooldown (avoid 288 alerts/day spam).
Alert timeout: 5s (avoid blocking tick on slow callback).
"""
import asyncio
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Callable, Awaitable

from .config import BearHunterConfig
from .state import BearHunterState, utcnow

logger = logging.getLogger(__name__)

PRESENCE_ALERT_COOLDOWN_HOURS = 6
PRESENCE_ALERT_TIMEOUT_SECONDS = 5.0


class PresenceLevel(str, Enum):
    NORMAL = "normal"
    DAY2 = "day2"
    DAY3 = "day3"
    DAY4 = "day4"


AlertCallback = Callable[[PresenceLevel, float], Awaitable[None]]


@dataclass
class PresenceTracker:
    config: BearHunterConfig
    alert_callback: Optional[AlertCallback] = None
    alert_timeout_seconds: float = PRESENCE_ALERT_TIMEOUT_SECONDS

    def hours_absent(self, state: BearHunterState) -> float:
        if not state.last_user_seen_at:
            return 0.0
        delta = utcnow() - state.last_user_seen_at
        return max(0.0, delta.total_seconds() / 3600.0)

    def current_level(self, state: BearHunterState) -> PresenceLevel:
        h = self.hours_absent(state)
        if h >= self.config.presence_day4_hours:
            return PresenceLevel.DAY4
        if h >= self.config.presence_day3_hours:
            return PresenceLevel.DAY3
        if h >= self.config.presence_warning_hours:
            return PresenceLevel.DAY2
        return PresenceLevel.NORMAL

    def heartbeat(self, state: BearHunterState) -> None:
        """User returned. Resets last_user_seen_at.

        Does NOT auto-resume positions closed by DAY3/DAY4.
        Does NOT clear kill switch.
        Does NOT clear waiting_liquidity (that's exchange-side, not presence).
        User must explicitly set_signal or reset_kill_switch to resume.
        """
        state.last_user_seen_at = utcnow()
        # Reset alert cooldown: new absence period -> new alert allowed immediately
        state.last_presence_alert_at = None

    def should_block_new_entries(self, state: BearHunterState) -> bool:
        """Interface for pre_flight Phase A presence check.
        True at DAY2, DAY3, DAY4.
        """
        return self.current_level(state) in (
            PresenceLevel.DAY2, PresenceLevel.DAY3, PresenceLevel.DAY4,
        )

    def should_close_profitable(self, state: BearHunterState) -> bool:
        """Interface for runner: at DAY3, close only profitable positions."""
        return self.current_level(state) == PresenceLevel.DAY3

    def should_close_all(self, state: BearHunterState) -> bool:
        """Interface for runner: at DAY4, close all positions and go idle."""
        return self.current_level(state) == PresenceLevel.DAY4

    async def check_and_alert(self, state: BearHunterState) -> PresenceLevel:
        """Evaluate presence, fire alert (rate-limited + timeout), return current level."""
        level = self.current_level(state)
        if level == PresenceLevel.NORMAL:
            return level
        if not self.alert_callback:
            return level

        now = utcnow()
        if state.last_presence_alert_at:
            elapsed_h = (now - state.last_presence_alert_at).total_seconds() / 3600.0
            if elapsed_h < PRESENCE_ALERT_COOLDOWN_HOURS:
                logger.debug(f"alert skipped (cooldown, {elapsed_h:.1f}h since last)")
                return level

        try:
            await asyncio.wait_for(
                self.alert_callback(level, self.hours_absent(state)),
                timeout=self.alert_timeout_seconds,
            )
            state.last_presence_alert_at = now
        except asyncio.TimeoutError:
            logger.warning(f"alert_callback timed out after {PRESENCE_ALERT_TIMEOUT_SECONDS}s")
        except Exception as e:
            logger.warning(f"alert_callback failed: {type(e).__name__}: {e}")

        return level
