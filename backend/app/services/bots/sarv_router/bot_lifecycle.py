"""BotLifecycleManager — start/stop bots based on regime + stability + cooldown."""
from typing import Callable

from app.services.bots.sarv_router.config import SarvRouterConfig
from app.services.bots.sarv_router.regime import Regime


def _regime_str(regime: Regime) -> str:
    return regime.value if hasattr(regime, "value") else str(regime)


class BotLifecycleManager:
    """Orchestrate bot start/stop with stability + cooldown guards."""

    def __init__(
        self,
        config: SarvRouterConfig,
        start_bot: Callable[[str], None],
        stop_bot: Callable[[str], None],
        stop_all: Callable[[], None],
    ):
        self.config = config
        self.start_bot = start_bot
        self.stop_bot = stop_bot
        self.stop_all = stop_all
        self._current_regime: Regime | None = None
        self._regime_since_idx: int | None = None
        self._last_switch_idx: int | None = None
        self.active_bots: list[str] = []

    def _desired_bots(self, regime: Regime) -> list[str]:
        if regime == Regime.UPTREND and self.config.uptrend_bot:
            return [self.config.uptrend_bot]
        if regime == Regime.RANGE and self.config.range_bot:
            return [self.config.range_bot]
        return []

    def update(self, regime: Regime, now_idx: int) -> dict:
        # 1) Regime changed → reset stability timer
        if regime != self._current_regime:
            self._current_regime = regime
            self._regime_since_idx = now_idx
            return {
                "action": "pending",
                "reason": "regime_changed",
                "regime": _regime_str(regime),
                "active_bots": list(self.active_bots),
            }

        desired = self._desired_bots(regime)

        # 2) Already active? → no_change (short-circuit)
        if sorted(desired) == sorted(self.active_bots):
            return {
                "action": "no_change",
                "regime": _regime_str(regime),
                "active_bots": list(self.active_bots),
            }

        # 3) Stability window
        stable = now_idx - (self._regime_since_idx or 0)
        if stable < self.config.stability_window:
            return {
                "action": "pending",
                "reason": "stability_window",
                "stable_candles": stable,
                "needed": self.config.stability_window,
                "regime": _regime_str(regime),
                "active_bots": list(self.active_bots),
            }

        # 4) Cooldown after last switch
        if self._last_switch_idx is not None:
            since_switch = now_idx - self._last_switch_idx
            if since_switch < self.config.cooldown_candles:
                return {
                    "action": "cooldown",
                    "since_switch": since_switch,
                    "needed": self.config.cooldown_candles,
                    "regime": _regime_str(regime),
                    "active_bots": list(self.active_bots),
                }

        # 5) Switch (fail-safe)
        prev = list(self.active_bots)
        try:
            self.stop_all()
            for slug in desired:
                self.start_bot(slug)
            self.active_bots = list(desired)
            self._last_switch_idx = now_idx
            return {
                "action": "switched",
                "from": prev,
                "to": list(desired),
                "regime": _regime_str(regime),
                "active_bots": list(self.active_bots),
            }
        except Exception as e:
            try:
                self.stop_all()
            except Exception:
                pass
            self.active_bots = []
            return {
                "action": "error",
                "error": f"{type(e).__name__}: {e}",
                "regime": _regime_str(regime),
                "active_bots": [],
            }
