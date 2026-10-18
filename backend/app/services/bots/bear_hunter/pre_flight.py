import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Optional, Any, List
from app.domain.ports.margin_exchange import (
    MarginExchangePort, DryRunResult, DryRunError, DryRunReason
)
from .config import BearHunterConfig
from .state import BearHunterState
from .audit import audit_trail

logger = logging.getLogger(__name__)
LIQUIDITY_CACHE_TTL = 300


@dataclass
class PreFlightResult:
    approved: bool
    reason: str = ""
    phase: str = ""
    check_index: int = -1  # ← which check number failed (0-based)
    dry_run_data: Optional[DryRunResult] = None
    checks_passed: List[str] = field(default_factory=list)


def _D(x) -> Decimal:
    return x if isinstance(x, Decimal) else Decimal(str(x))


def _liquidity_is_fresh_and_negative(state: BearHunterState, market: str) -> bool:
    info = state.last_known_liquidity.get(market)
    if not info:
        return False
    try:
        checked_at = datetime.fromisoformat(info.get("checked_at", ""))
    except ValueError:
        return False
    if (utcnow_safe() - checked_at) > timedelta(seconds=LIQUIDITY_CACHE_TTL):
        return False
    return info.get("available") is False


def utcnow_safe() -> datetime:
    return datetime.now(timezone.utc)


def _record_liquidity(state: BearHunterState, market: str, available: bool) -> None:
    state.last_known_liquidity[market] = {
        "available": available,
        "checked_at": utcnow_safe().isoformat(),
    }


def _synthetic_dry_run(signal, config) -> DryRunResult:
    """Paper mode: synthetic dry_run (no real API call)."""
    entry = float(signal.entry_price)
    size = float(signal.size_tmn)
    return DryRunResult(
        liquidity_price=entry * 2.0,
        call_price=entry * 1.5,
        open_fee=size * 0.002,
        trade_fee=size * 0.002,
        extend_fee=0.0,
        loan_amount=size * (config.risk_coef - 1),
        max_age=86400,
        risk_coef=config.risk_coef,
    )


async def pre_flight_check(
    signal: Any,
    state: BearHunterState,
    config: BearHunterConfig,
    adapter: MarginExchangePort,
) -> PreFlightResult:
    passed = []
    now = utcnow_safe()

    async def _reject(reason: str, phase: str) -> PreFlightResult:
        res = PreFlightResult(
            approved=False, reason=reason, phase=phase,
            check_index=len(passed), checks_passed=passed,
        )
        await audit_trail.log_entry(False, phase, reason, signal, config, state)
        return res

    # ─── Phase A ───
    if not state.initialized:
        return await _reject("not_initialized", "A")
    passed.append("initialized")
    if state.is_killed:
        return await _reject("kill_switch_auto" if state.kill_switch_auto else "kill_switch_manual", "A")
    passed.append("kill_switch")
    if state.idle:
        return await _reject("idle", "A")
    passed.append("idle")
    if state.paper_mode and not getattr(signal, "is_paper", False):
        return await _reject("paper_mode_violation", "A")
    passed.append("paper_mode")

    # Phase 0: HumanSignal
    if not state.human_signal:
        return await _reject("no_human_signal", "A")
    passed.append("human_signal_present")
    if state.human_signal.expires_at <= now:
        return await _reject("human_signal_expired", "A")
    passed.append("human_signal_not_expired")
    if state.human_signal.direction != "bearish":
        return await _reject(f"signal_is_{state.human_signal.direction}", "A")
    passed.append("signal_bearish")
    # NOTE: check 6 (current_regime != "bear") removed — it's redundant with signal_bearish
    # since current_regime is derived from human_signal.direction.

    if state.last_user_seen_at:
        hours_absent = (now - state.last_user_seen_at).total_seconds() / 3600
        if hours_absent > config.presence_warning_hours:
            return await _reject("user_absent", "A")
    passed.append("presence")
    if getattr(signal, "age_seconds", 0) > 300:
        return await _reject("stale_signal", "A")
    passed.append("signal_freshness")

    # ─── Phase B ───
    size = _D(signal.size_tmn)
    if size > _D(config.per_order_limit_tmn):
        return await _reject("per_order_limit_exceeded", "B")
    passed.append("per_order_limit")
    if _D(state.daily_volume_tmn) + size > _D(config.daily_volume_limit_tmn):
        return await _reject("daily_volume_limit_exceeded", "B")
    passed.append("daily_volume_limit")
    if len(state.open_positions) >= config.max_open_positions:
        return await _reject("max_open_positions_reached", "B")
    passed.append("max_positions")
    if any(p.market == signal.market for p in state.open_positions):
        return await _reject("same_market_already_open", "B")
    passed.append("same_market")
    if state.last_trade_at:
        if (now - state.last_trade_at).total_seconds() < config.cooldown_seconds:
            return await _reject("cooldown_active", "B")
    passed.append("cooldown")
    if state.trades_today >= config.max_trades_per_day:
        return await _reject("max_trades_today_reached", "B")
    passed.append("max_trades_today")
    if state.pnl_8h_pct <= config.loss_limit_8h_pct:
        return await _reject("8h_loss_limit_hit", "B")
    passed.append("8h_loss_limit")
    if _D(getattr(signal, "sl_pct", 0)) < _D(config.mandatory_sl_pct):
        return await _reject("sl_below_mandatory", "B")
    passed.append("sl_mandatory")
    if _D(getattr(signal, "tp_pct", 0)) < _D(config.mandatory_tp_pct):
        return await _reject("tp_below_mandatory", "B")
    passed.append("tp_mandatory")
    projected_loss = size * (_D(config.mandatory_sl_pct) / _D("100"))
    max_daily_loss = (_D(config.daily_loss_limit_pct) / _D("100")) * _D(state.capital_tmn)
    current_daily_pnl = (_D(state.daily_pnl_pct) / _D("100")) * _D(state.capital_tmn)
    if (current_daily_pnl - projected_loss) < -max_daily_loss:
        return await _reject("projected_daily_loss_limit", "B")
    passed.append("projected_loss")

    # ─── Phase C ───
    try:
        if state.paper_mode:
            balance_val = 200_000.0
            spread = 0.1
        else:
            balance_val = await adapter.get_balance()
            ob = await adapter.get_order_book(signal.market)
            spread = getattr(ob, "spread_pct", 0)
        if _D(balance_val) < size:
            return await _reject("insufficient_collateral", "C")
        passed.append("collateral")
        if spread > 0.5:
            return await _reject("wide_spread", "C")
        passed.append("order_book")
    except Exception as e:
        return await _reject(f"phase_c_api_error_{type(e).__name__}", "C")

    if _liquidity_is_fresh_and_negative(state, signal.market):
        return await _reject("no_margin_liquidity_cached", "C")
    passed.append("liquidity_cache")

    # ─── Phase D ───
    try:
        if state.paper_mode and getattr(config, "paper_skip_dry_run", True):
            dry = _synthetic_dry_run(signal, config)
        else:
            dry = await adapter.dry_run(
                collateral=str(size), market=signal.market, open_price=str(signal.entry_price),
                risk_coef=str(config.risk_coef), side="short",
                stop_loss=str(signal.stop_loss), take_profit=str(signal.take_profit),
            )
        _record_liquidity(state, signal.market, available=True)
        state.clear_waiting_liquidity()
    except DryRunError as e:
        if e.reason == DryRunReason.NO_LIQUIDITY:
            _record_liquidity(state, signal.market, available=False)
            state.mark_waiting_liquidity()
            return await _reject("no_margin_liquidity", "D")
        if e.reason == DryRunReason.UNAUTHORIZED:
            state.mark_kill_switch("dry_run_unauthorized", source="auto")
            return await _reject("dry_run_unauthorized", "D")
        return await _reject(f"dry_run_{e.reason.value}", "D")
    except Exception as e:
        return await _reject(f"dry_run_failed_{type(e).__name__}", "D")
    passed.append("dry_run")

    entry = _D(signal.entry_price)
    sl_dist = abs(entry - _D(signal.stop_loss)) / entry
    liq_dist = abs(entry - _D(dry.liquidity_price)) / entry
    if sl_dist > (liq_dist * _D(config.sl_to_liq_ratio)):
        return await _reject("sl_too_close_to_liq", "D")
    passed.append("sl_to_liq_ratio")
    current_to_call = abs(_D(signal.current_price) - _D(dry.call_price)) / _D(signal.current_price)
    if current_to_call < _D("0.05"):
        return await _reject("too_close_to_call_price", "D")
    passed.append("call_price_proximity")
    if _D(getattr(dry, "borrow_fee_pct_24h", 0)) > _D("0.5"):
        return await _reject("borrow_fee_too_high", "D")
    passed.append("borrow_fee")
    if getattr(dry, "extend_time", 99999) < 3600:
        return await _reject("extend_time_too_short", "D")
    passed.append("extend_time")

    # ─── Phase E ───
    await audit_trail.log_entry(True, "E", "approved", signal, config, state, dry)
    return PreFlightResult(approved=True, reason="", phase="E", dry_run_data=dry, checks_passed=passed)
