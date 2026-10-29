"""SarvTigerConfig — aggressive BTC futures, 4 hard safety rules.

Safety rules baked in (non-negotiable):
  1. SL mandatory (sl_atr_mult > 0)
  2. Position size <= 20% (hard check in __post_init__)
  3. Daily loss limit <= 10% (hard cap)
  4. Max leverage = 4x (hard cap, riskier)
"""
from dataclasses import dataclass


@dataclass(slots=True)
class SarvTigerConfig:
    # Instrument — BTC only, 4h timeframe
    symbol: str = "BTCTMN"
    timeframe: str = "4h"

    # Position — risky but controlled
    leverage: int = 4
    max_leverage: int = 4          # HARD CAP (riskier)
    position_size_pct: float = 20.0  # 20% (at safety limit)
    max_positions: int = 1

    # Safety (SL/TP/daily/DD)
    sl_atr_mult: float = 1.2        # SL = 1.2 × ATR (tighter, more stops but smaller)
    tp_atr_mult: float = 8.0        # TP = 8.0 × ATR → R/R = 6.67:1
    daily_loss_limit_pct: float = 7.0
    max_drawdown_pct: float = 25.0

    # Bollinger Squeeze
    bb_period: int = 20
    bb_std: float = 2.0
    bb_squeeze_window: int = 20
    bb_squeeze_threshold: float = 0.5  # width < 0.5×avg → squeeze

    # ATR
    atr_period: int = 14

    # Pyramiding
    pyramiding_enabled: bool = True
    pyramiding_add_pct: float = 30.0   # add 30% of initial size
    pyramiding_step_atr: float = 1.5   # at each +1.5 ATR from entry

    # Trailing
    trailing_enabled: bool = True
    trailing_atr_mult: float = 2.0

    def __post_init__(self) -> None:
        # Hard safety checks — fail-fast if violated
        if self.leverage > self.max_leverage:
            raise ValueError(
                f"leverage {self.leverage} > max {self.max_leverage} (safety rule 4)"
            )
        if self.position_size_pct <= 0 or self.position_size_pct > 20.0:
            raise ValueError(
                f"position_size_pct {self.position_size_pct} must be (0, 20] (safety rule 2)"
            )
        if self.sl_atr_mult <= 0:
            raise ValueError("sl_atr_mult must be > 0 (safety rule 1)")
        if self.daily_loss_limit_pct <= 0 or self.daily_loss_limit_pct > 10.0:
            raise ValueError(
                f"daily_loss_limit_pct {self.daily_loss_limit_pct} must be (0, 10] (safety rule 3)"
            )
