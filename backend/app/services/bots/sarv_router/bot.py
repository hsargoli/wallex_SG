"""SarvRouter — Regime-Based Bot Orchestrator (integration layer)."""
import uuid
from pathlib import Path
from typing import Callable

from app.domain.entities.candle import Candle
from app.services.bots.sarv_router.audit import AuditEntry, AuditTrail
from app.services.bots.sarv_router.bot_lifecycle import BotLifecycleManager
from app.services.bots.sarv_router.capital_allocator import allocate_capital
from app.services.bots.sarv_router.config import SarvRouterConfig
from app.services.bots.sarv_router.decision import DecisionReason
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

    def _decision(
        self,
        action: str,
        why: str,
        evidence: dict,
        confidence: float = 1.0,
    ) -> dict:
        """Wrap a decision in DecisionReason per ADR-0040 Addendum 1.1."""
        return DecisionReason(
            action=action,
            why=why,
            evidence=evidence,
            confidence=confidence,
            tick_id=str(uuid.uuid4()),
        ).to_dict()

    def tick(
        self,
        user_id: str,
        candles: list[Candle],
        now_idx: int,
    ) -> dict:
        """One tick: load state → check kill → detect regime → update lifecycle."""
        state = self.store.load(user_id)
        # Test B: restore internal lifecycle state on restart
        self.lifecycle.hydrate_from_state(state)

        # 1) Kill switch (manual or auto)
        if state.kill_switch_manual or state.kill_switch_auto:
            self._safe_stop_all()
            self.lifecycle.active_bots = []
            kill_reason = "manual" if state.kill_switch_manual else "auto"
            decision = self._decision(
                action="kill_switch_active",
                why=f"kill_switch_{kill_reason}",
                evidence={
                    "reason": kill_reason,
                    "regime": state.current_regime,
                    "active_bots": [],
                    "path": "kill_switch",
                },
            )
            state.last_decision = decision
            self.store.save(user_id, state)
            return decision

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
            decision = self._decision(
                action="daily_loss_kill",
                why=f"daily_loss={state.daily_pnl_pct}",
                evidence={
                    "daily_pnl_pct": state.daily_pnl_pct,
                    "regime": state.current_regime,
                    "active_bots": [],
                    "path": "daily_loss",
                },
            )
            state.last_decision = decision
            self.store.save(user_id, state)
            return decision

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
        # Sync lifecycle internal state back to persistent state
        # NOTE: interpretation (relative) only. For absolute (reset on restart),
        # see Test B (future, not in this commit).
        state.regime_since_idx = self.lifecycle.regime_since_idx

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
        decision = self._decision(
            action=action.get("action", "unknown"),
            why=str(action.get("reason", action.get("action", ""))),
            evidence={**action, "path": "lifecycle", "regime": regime_str},
        )
        state.last_decision = decision
        self.store.save(user_id, state)
        return decision
