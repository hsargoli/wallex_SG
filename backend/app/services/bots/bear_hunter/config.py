from dataclasses import dataclass

@dataclass(frozen=True)
class BearHunterConfig:
    # ── لایه ۱: قوانین قطعی ──
    # Aligned with 5M capital (ADR 0023)
    daily_volume_limit_tmn: float = 1_500_000  # 30%
    per_order_limit_tmn: float = 500_000       # 10%
    max_open_positions: int = 4
    cooldown_seconds: int = 60
    loss_limit_8h_pct: float = -5.0
    
    # SL/TP اجباری
    mandatory_sl_pct: float = 3.0
    mandatory_tp_pct: float = 4.5
    
    audit_trail_enabled: bool = True
    dry_run_mandatory: bool = True

    
    # ── کارمزدها ──
    entry_fee_pct: float = 0.2
    exit_fee_pct: float = 0.2
    borrow_hourly_pct: float = 0.01

    # ── ATR + Trailing (borrowed from Nooaah) ──
    sl_atr_mult: float = 1.5
    tp_atr_mult: float = 3.0
    use_trailing: bool = True
    trailing_atr_mult: float = 3.0  # Wider trailing to avoid noise
    volume_z_min: float = -0.5
    adx_min: float = 25.0
    rsi_overbought: float = 70.0  # Standard for scalping waves
    use_scalping: bool = True
    
    # Margin specific
    risk_coef: int = 1
    max_hold_hours: int = 6
    sl_to_liq_ratio: float = 0.5

    # ── لایه ۲: قابل تنظیم ──
    position_size_pct: float = 15.0  # percent (15.0 = 15%)
    max_trades_per_day: int = 5
    daily_loss_limit_pct: float = 3.0

    # ── لایه ۳: Regime Router Rules (Presence) ──
    presence_warning_hours: int = 48
    presence_day3_hours: int = 72
    presence_day4_hours: int = 96
    regime_switch_grace_hours: int = 6
    regime_switch_warning_minutes: int = 5

    def __post_init__(self):
        if self.risk_coef > 2:
            raise ValueError("risk_coef (leverage) cannot exceed 2 for bear_hunter")
        if self.per_order_limit_tmn > self.daily_volume_limit_tmn:
            raise ValueError("per_order_limit cannot be greater than daily_volume_limit")
