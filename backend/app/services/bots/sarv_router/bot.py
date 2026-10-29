"""SarvRouter — Regime-Based Bot Orchestrator (integration layer)."""
from pathlib import Path
from typing import Callable

from app.domain.entities.candle import Candle
from app.services.bots.sarv_router.audit import AuditEntry, AuditTrail
from app.services.bots.sarv_router.bot_lifecycle import BotLifecycleManager
from app.services.bots.sarv_router.capital_allocator import allocate_capital
from app.services.bots.sarv_router.config import SarvRouterConfig
from app.services.bots.sarv_router.gate import write_gate
from app.services.bots.sarv_router.regime import Regime, detect_regime, detect_regime_multi_tf
from app.services.bots.sarv_router.store import SarvState, SarvStore


class SarvRouter:
    """Orchestrator: regime → lifecycle → capital + store + audit."""

    def __init__(
        self,
        config: SarvRouterConfig,
        start_bot: Callable[[str], None],
        stop_bot: Callable[[str], None],
        stop_all: Callable[[], None],
        store: SarvStore | None = None,
        audit: AuditTrail | None = None,
    ):
        self.config = config
        self.store = store or SarvStore()
        self.audit = audit or AuditTrail()
        self._stop_all_raw = stop_all
        self.lifecycle = BotLifecycleManager(
            config=config,
            start_bot=start_bot,
            stop_bot=stop_bot,
            stop_all=stop_all,
        )

    def _safe_stop_all(self) -> None:
        try:
            self._stop_all_raw()
        except Exception:
            pass

    def tick(
        self,
        user_id: str,
        candles: list[Candle],
        now_idx: int,
    ) -> dict:
        """One tick: load state → check kill → detect regime → update lifecycle."""
        state = self.store.load(user_id)

        # 1) Kill switch (manual or auto)
        if state.kill_switch_manual or state.kill_switch_auto:
            self._safe_stop_all()
            self.lifecycle.active_bots = []
            return {
                "action": "kill_switch_active",
                "reason": "manual" if state.kill_switch_manual else "auto",
            }

        # 2) Daily loss limit
        if state.daily_pnl_pct <= -self.config.daily_loss_limit_pct:
            state.kill_switch_auto = True
            self.store.save(user_id, state)
            self._safe_stop_all()
            prev_bots = list(self.lifecycle.active_bots)
            self.lifecycle.active_bots = []
            self.audit.log(user_id, AuditEntry(
                type="kill_switch",
                from_regime=state.current_regime,
                to_regime=state.current_regime,
                from_bots=prev_bots,
                to_bots=[],
                reason="daily_loss_limit",
                allocations={},
                cash=state.total_capital,
            ))
            return {
                "action": "daily_loss_kill",
                "daily_pnl_pct": state.daily_pnl_pct,
            }

        # 3) Detect regime + lifecycle
        if getattr(self.config, "enable_multi_tf", False):
            regime = detect_regime_multi_tf(candles, self.config)
        else:
            regime = detect_regime(candles, self.config)
        regime_str = regime.value if hasattr(regime, "value") else str(regime)
        # Write gate: only uptrend allows new entries (Phase 2A)
        write_gate(allow_new_entries=(regime == Regime.UPTREND), regime=regime_str)
        prev_regime = state.current_regime
        prev_bots = list(self.lifecycle.active_bots)

        # Always track detected regime (even on no_change/pending)
        state.current_regime = regime_str
        action = self.lifecycle.update(regime, now_idx)

        # 4) On switch: allocate
        if action.get("action") == "switched":
            alloc = allocate_capital(state.total_capital, regime, self.config)
            state.active_bots = alloc["active_bots"]
            state.allocations = alloc["allocations"]
            state.cash = alloc["cash"]
            state.last_switch_idx = now_idx
            self.audit.log(user_id, AuditEntry(
                type="switch",
                from_regime=prev_regime,
                to_regime=regime_str,
                from_bots=prev_bots,
                to_bots=alloc["active_bots"],
                reason="lifecycle_switch",
                allocations=alloc["allocations"],
                cash=alloc["cash"],
            ))

        # Always persist (regime + any switch changes)
        self.store.save(user_id, state)
        return action
