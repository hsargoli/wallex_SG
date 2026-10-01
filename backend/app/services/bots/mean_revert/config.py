"""تنظیمات Mean Revert Bot."""

from dataclasses import dataclass


@dataclass(slots=True)
class MeanRevertConfig:
    """تنظیمات پیش‌فرض کف‌زن."""

    timeframe: str = "15m"
    check_interval_sec: int = 180
    max_positions: int = 3
    position_size_pct: float = 30.0
    fee_pct: float = 0.2
    max_duration_candles: int = 20
    warmup_candles: int = 50
    # آستانه‌های انتخاب استراتژی
    min_avg_return: float = 0.3
    min_stability: float = 0.5
