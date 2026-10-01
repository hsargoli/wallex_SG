"""تنظیمات Trend Follow Bot."""

from dataclasses import dataclass


@dataclass(slots=True)
class TrendFollowConfig:
    """تنظیمات پیش‌فرض روندرو."""

    timeframe: str = "1h"
    check_interval_sec: int = 300
    max_positions: int = 3
    position_size_pct: float = 30.0
    fee_pct: float = 0.2

    ema_fast: int = 20
    ema_slow: int = 50

    adx_period: int = 14
    adx_threshold: float = 25.0

    sl_atr_mult: float = 2.0
    trail_atr_mult: float = 2.0
    use_trailing: bool = True

    max_duration_candles: int = 168
    warmup_candles: int = 100
