"""تنظیمات Scalp Master v2."""

from dataclasses import dataclass


@dataclass(slots=True)
class ScalpMasterConfig:
    """تنظیمات Scalp Master v2."""

    timeframe: str = "1h"

    # تشخیص سقوط
    lookback_high: int = 20
    drop_threshold_pct: float = 2.5

    # RSI
    rsi_period: int = 14
    rsi_min: float = 25.0
    rsi_max: float = 50.0

    # کیفیت کندل
    min_body_ratio: float = 0.3

    # SL/TP پویا (ATR-based)
    sl_atr_mult: float = 1.5
    tp_atr_mult: float = 3.0
    min_sl_pct: float = 1.5

    # فیلتر سقوط آزاد
    max_dist_from_ema: float = 5.0

    # Timeout
    timeout_candles: int = 24

    # ریسک
    position_size_pct: float = 30.0
    fee_pct: float = 0.2

    # Warmup
    warmup_candles: int = 60
