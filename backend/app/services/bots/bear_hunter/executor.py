import logging
from decimal import Decimal
from datetime import datetime, timezone
from typing import Optional
from app.domain.ports.margin_exchange import MarginExchangePort, MarginPosition
from .config import BearHunterConfig
from .state import BearHunterState
from .audit import audit_trail
from .pre_flight import PreFlightResult

logger = logging.getLogger(__name__)

def _make_paper_position(signal, config: BearHunterConfig) -> MarginPosition:
    """ایجاد یک پوزیشن مجازی برای حالت paper_mode."""
    entry = float(signal.entry_price)
    sl = float(signal.stop_loss)
    tp = float(signal.take_profit)
    return MarginPosition(
        position_id=f"paper-{datetime.now(timezone.utc).timestamp()}",
        market=signal.market,
        side="short",
        collateral=float(signal.size_tmn),
        entry_price=entry,
        current_price=entry,
        liquidation_price=entry * 2.0,  # فرض: 100% حرکت خلاف = لیکویید
        call_price=entry * 1.5,
        risk_coef=config.risk_coef,
        profit_percentage=0.0,
        loan_amount=float(signal.size_tmn) * (config.risk_coef - 1),
        interest=0.0,
        stop_loss=sl,
        take_profit=tp,
        state="open",
        extend_time=0
    )

async def execute_short_entry(
    signal,
    pre_flight: PreFlightResult,
    state: BearHunterState,
    config: BearHunterConfig,
    adapter: MarginExchangePort
) -> Optional[MarginPosition]:
    if not pre_flight.approved:
        logger.error("Execution blocked: pre_flight not approved.")
        return None

    audit_id = await audit_trail.log_trade_intent(signal, pre_flight.dry_run_data)

    try:
        if state.paper_mode:
            logger.info("Paper Mode active: generating virtual position.")
            pos = _make_paper_position(signal, config)
        else:
            # Live Mode
            pos = await adapter.open_position(
                collateral=str(signal.size_tmn),
                market=signal.market,
                open_price=str(signal.entry_price),
                risk_coef=str(config.risk_coef),
                side="short",
                stop_loss=str(signal.stop_loss),
                take_profit=str(signal.take_profit)
            )
        
        state.open_positions.append(pos)
        state.trades_today += 1
        state.daily_volume_tmn += float(signal.size_tmn)
        state.last_trade_at = datetime.now(timezone.utc)
        
        await audit_trail.log_trade_success(audit_id, pos)
        logger.info(f"Successfully {'simulated' if state.paper_mode else 'opened'} short {pos.position_id}")
        return pos

    except Exception as e:
        logger.error(f"Failed to open short: {e}")
        await audit_trail.log_trade_failure(audit_id, str(e))
        return None


async def close_paper_position(
    position_id: str,
    exit_price: Decimal,
    state: BearHunterState,
    config: BearHunterConfig,
) -> Optional[Decimal]:
    """Close a virtual paper position locally (no API call). Returns net PnL."""
    from .rules import calculate_short_net_pnl
    
    # Find position
    target_pos = None
    for i, pos in enumerate(state.open_positions):
        if pos.position_id == position_id:
            target_pos = pos
            state.open_positions.pop(i)
            break
    
    if not target_pos:
        return None
    
    # Calculate PnL
    hours_held = 1  # Simplified
    pnl_obj = calculate_short_net_pnl(
        entry_price=Decimal(str(target_pos.entry_price)),
        exit_price=exit_price,
        position_size_tmn=Decimal(str(target_pos.collateral)),
        hours_held=hours_held,
        capital_tmn=Decimal(str(state.capital_tmn)),
        config=config,
    )
    
    state.capital_tmn += float(pnl_obj.net_pnl)
    state.pnl_8h_pct += float(pnl_obj.net_pnl_pct_of_capital)
    state.daily_pnl_pct += float(pnl_obj.net_pnl_pct_of_capital)
    
    await audit_trail.log_entry(
        True, "PAPER_CLOSE", f"Closed {position_id} at {exit_price}",
        {"position_id": position_id, "pnl": float(pnl_obj.net_pnl)},
        config, state,
    )
    
    return pnl_obj.net_pnl
