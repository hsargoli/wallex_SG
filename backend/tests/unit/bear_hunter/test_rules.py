import pytest
from decimal import Decimal
from dataclasses import dataclass
from app.services.bots.bear_hunter.rules import (
    calculate_position_size, calculate_short_levels, calculate_fees,
    calculate_short_net_pnl, calculate_breakeven_win_rate,
    check_rr_ratio, check_sl_to_liq_ratio,
)

@dataclass
class FakeConfig:
    position_size_pct: float = 15.0
    per_order_limit_tmn: float = 100_000.0
    risk_coef: int = 1
    mandatory_sl_pct: float = 3.0
    mandatory_tp_pct: float = 4.5  # Updated to 4.5
    entry_fee_pct: float = 0.2
    exit_fee_pct: float = 0.2
    borrow_hourly_pct: float = 0.01

CFG = FakeConfig()
D = Decimal

def test_position_size_capital_cap():
    s = calculate_position_size(D("100000"), CFG, D("300000"), D("21562618329"))
    assert s.size_tmn == D("15000.00")
    assert s.cap_reason == "capital"
    assert s.was_capped is False

def test_position_size_per_order_cap():
    s = calculate_position_size(D("1000000"), CFG, D("3000000"), D("21562618329"))
    assert s.size_tmn == D("100000.00")
    assert s.cap_reason == "per_order"
    assert s.was_capped is True

def test_position_size_daily_remaining_cap():
    s = calculate_position_size(D("100000"), CFG, D("5000"), D("21562618329"))
    assert s.size_tmn == D("5000.00")
    assert s.cap_reason == "daily_remaining"

def test_position_size_below_minimum():
    s = calculate_position_size(D("100000"), CFG, D("300000"), D("21562618329"), min_order_value_tmn=D("20000"))
    assert s.size_tmn == D("0")
    assert s.below_minimum is True

def test_position_size_zero_capital():
    s = calculate_position_size(D("0"), CFG, D("300000"), D("21562618329"))
    assert s.size_tmn == D("0")

def test_position_size_collateral_with_leverage():
    cfg = FakeConfig(risk_coef=2)
    s = calculate_position_size(D("100000"), cfg, D("300000"), D("21562618329"))
    assert s.size_tmn == D("15000.00")
    assert s.collateral_tmn == D("7500.00")

def test_short_levels_direction():
    lv = calculate_short_levels(D("1000"), CFG)
    assert lv.stop_loss > lv.entry
    assert lv.take_profit < lv.entry
    assert lv.stop_loss == D("1030.00")
    assert lv.take_profit == D("955.00") # 1000 * (1 - 0.045)

def test_fees_calculation():
    f = calculate_fees(D("15000"), 0, CFG)
    assert f.entry_fee == D("30.00")
    assert f.exit_fee == D("30.00")
    assert f.borrow_fee == D("0.00")
    assert f.total == D("60.00")

def test_fees_with_borrow():
    f = calculate_fees(D("15000"), 6, CFG)
    assert f.borrow_fee == D("9.00")
    assert f.total == D("69.00")

def test_short_pnl_profit():
    pnl = calculate_short_net_pnl(D("1000"), D("970"), D("15000"), 6, D("100000"), CFG)
    assert pnl.gross_pnl == D("450.00")
    assert pnl.net_pnl == D("381.00")
    assert pnl.net_pnl_pct_of_capital == D("0.38")

def test_short_pnl_loss():
    pnl = calculate_short_net_pnl(D("1000"), D("1030"), D("15000"), 6, D("100000"), CFG)
    assert pnl.gross_pnl == D("-450.00")
    assert pnl.net_pnl < 0

def test_breakeven_wr():
    p = calculate_breakeven_win_rate(D("450"), D("-450"))
    assert p == D("50.0")

def test_rr_ratio_with_sl_3_tp_45():
    lv = calculate_short_levels(D("1000"), CFG)
    f = calculate_fees(D("15000"), 6, CFG)
    passes, ratio = check_rr_ratio(lv, f, D("15000"), D("1.0"))
    assert passes is True
    assert ratio > Decimal("1.0")

def test_sl_to_liq_ratio():
    passes, ratio = check_sl_to_liq_ratio(D("1000"), D("1030"), D("1100"), D("0.5"))
    assert ratio == D("0.30")
    assert passes is True

def test_sl_to_liq_ratio_fails():
    passes, ratio = check_sl_to_liq_ratio(D("1000"), D("1030"), D("1040"), D("0.5"))
    assert ratio == D("0.75")
    assert passes is False
