"""
BearHunter Rules — pure math only.
CRITICAL: Pure functions, Decimal everywhere, no I/O, no state.
"""
from dataclasses import dataclass
from decimal import Decimal, ROUND_DOWN
from typing import Optional

@dataclass(frozen=True)
class PositionSizing:
    size_tmn: Decimal
    collateral_tmn: Decimal
    quantity: Decimal
    was_capped: bool
    cap_reason: Optional[str]
    below_minimum: bool

@dataclass(frozen=True)
class ShortLevels:
    entry: Decimal
    stop_loss: Decimal
    take_profit: Decimal
    sl_distance_pct: Decimal
    tp_distance_pct: Decimal

@dataclass(frozen=True)
class Fees:
    entry_fee: Decimal
    exit_fee: Decimal
    borrow_fee: Decimal
    total: Decimal

@dataclass(frozen=True)
class ShortPnL:
    gross_pnl: Decimal
    fees: Fees
    net_pnl: Decimal
    net_pnl_pct_of_position: Decimal
    net_pnl_pct_of_capital: Decimal

_HUNDRED = Decimal("100")
_ONE = Decimal("1")
_TMN_QUANT = Decimal("0.01")
_QTY_QUANT = Decimal("0.00000001")

def calculate_position_size(
    capital_tmn: Decimal,
    config,
    daily_remaining_tmn: Decimal,
    current_price: Decimal,
    min_order_value_tmn: Optional[Decimal] = None,
) -> PositionSizing:
    if capital_tmn <= 0 or current_price <= 0:
        return _empty_sizing("capital")
    
    from_capital = (capital_tmn * Decimal(str(config.position_size_pct)) / _HUNDRED).quantize(_TMN_QUANT, rounding=ROUND_DOWN)
    from_per_order = Decimal(str(config.per_order_limit_tmn)).quantize(_TMN_QUANT, rounding=ROUND_DOWN)
    from_daily = daily_remaining_tmn.quantize(_TMN_QUANT, rounding=ROUND_DOWN)
    
    size = min(from_capital, from_per_order, from_daily)
    
    cap_reason = None
    if size == from_per_order and size < from_capital:
        cap_reason = "per_order"
    elif size == from_daily and size < from_capital:
        cap_reason = "daily_remaining"
    elif size == from_capital:
        cap_reason = "capital"
    
    if min_order_value_tmn is not None and size < min_order_value_tmn:
        return PositionSizing(Decimal("0"), Decimal("0"), Decimal("0"), True, "below_minimum", True)
    
    collateral = (size / Decimal(str(config.risk_coef))).quantize(_TMN_QUANT, rounding=ROUND_DOWN)
    qty = (size / current_price).quantize(_QTY_QUANT, rounding=ROUND_DOWN)
    
    return PositionSizing(size, collateral, qty, size < from_capital, cap_reason, False)

def _empty_sizing(reason: str) -> PositionSizing:
    return PositionSizing(Decimal("0"), Decimal("0"), Decimal("0"), True, reason, False)

def calculate_short_levels(entry_price: Decimal, config) -> ShortLevels:
    sl_mult = _ONE + (Decimal(str(config.mandatory_sl_pct)) / _HUNDRED)
    tp_mult = _ONE - (Decimal(str(config.mandatory_tp_pct)) / _HUNDRED)
    
    sl = (entry_price * sl_mult).quantize(_TMN_QUANT, rounding=ROUND_DOWN)
    tp = (entry_price * tp_mult).quantize(_TMN_QUANT, rounding=ROUND_DOWN)
    
    return ShortLevels(entry_price, sl, tp, Decimal(str(config.mandatory_sl_pct)), Decimal(str(config.mandatory_tp_pct)))

def calculate_fees(position_size_tmn: Decimal, hours_held: int, config) -> Fees:
    hours = max(0, hours_held)
    entry_fee = (position_size_tmn * Decimal(str(config.entry_fee_pct)) / _HUNDRED).quantize(_TMN_QUANT, rounding=ROUND_DOWN)
    exit_fee = (position_size_tmn * Decimal(str(config.exit_fee_pct)) / _HUNDRED).quantize(_TMN_QUANT, rounding=ROUND_DOWN)
    borrow = (position_size_tmn * Decimal(str(config.borrow_hourly_pct)) / _HUNDRED * hours).quantize(_TMN_QUANT, rounding=ROUND_DOWN)
    return Fees(entry_fee, exit_fee, borrow, entry_fee + exit_fee + borrow)

def calculate_short_net_pnl(entry_price: Decimal, exit_price: Decimal, position_size_tmn: Decimal, hours_held: int, capital_tmn: Decimal, config) -> ShortPnL:
    price_diff_pct = (entry_price - exit_price) / entry_price
    gross = (price_diff_pct * position_size_tmn).quantize(_TMN_QUANT, rounding=ROUND_DOWN)
    fees = calculate_fees(position_size_tmn, hours_held, config)
    net = (gross - fees.total).quantize(_TMN_QUANT, rounding=ROUND_DOWN)
    
    net_pct_pos = (net / position_size_tmn * _HUNDRED).quantize(_TMN_QUANT, rounding=ROUND_DOWN) if position_size_tmn > 0 else Decimal("0")
    net_pct_cap = (net / capital_tmn * _HUNDRED).quantize(_TMN_QUANT, rounding=ROUND_DOWN) if capital_tmn > 0 else Decimal("0")
    
    return ShortPnL(gross, fees, net, net_pct_pos, net_pct_cap)

def calculate_breakeven_win_rate(avg_net_win: Decimal, avg_net_loss: Decimal) -> Decimal:
    R = abs(avg_net_win)
    L = abs(avg_net_loss)
    if R + L == 0: return Decimal("0")
    return (L / (R + L) * _HUNDRED).quantize(Decimal("0.1"), rounding=ROUND_DOWN)

def check_rr_ratio(levels: ShortLevels, fees: Fees, position_size_tmn: Decimal, min_ratio: Decimal) -> tuple[bool, Decimal]:
    gross_reward = (levels.tp_distance_pct / _HUNDRED) * position_size_tmn
    gross_risk = (levels.sl_distance_pct / _HUNDRED) * position_size_tmn
    
    net_reward = gross_reward - fees.total
    net_risk = gross_risk + fees.total
    
    if net_risk <= 0: return False, Decimal("0")
    ratio = (net_reward / net_risk).quantize(Decimal("0.01"), rounding=ROUND_DOWN)
    return ratio >= min_ratio, ratio

def check_sl_to_liq_ratio(entry: Decimal, stop_loss: Decimal, liquidation_price: Decimal, ratio_threshold: Decimal) -> tuple[bool, Decimal]:
    dist_sl = abs(stop_loss - entry)
    dist_liq = abs(liquidation_price - entry)
    if dist_liq == 0: return False, Decimal("inf")
    ratio = (dist_sl / dist_liq).quantize(Decimal("0.01"), rounding=ROUND_DOWN)
    return ratio <= ratio_threshold, ratio
