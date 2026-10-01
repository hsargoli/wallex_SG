"""تنظیمات Grid Bot."""

from dataclasses import dataclass


@dataclass(slots=True)
class GridBotConfig:
    """تنظیمات پیش‌فرض شبکه‌ای."""

    timeframe: str = "15m"
    check_interval_sec: int = 180
    fee_pct: float = 0.2

    # Grid levels
    n_buy_levels: int = 3
    n_sell_levels: int = 2
    grid_spacing_atr: float = 1.0  # فاصله بین سطوح = 1× ATR

    # Position sizing
    capital_per_level_pct: float = 15.0  # 15% سرمایه در هر سطح

    # Detection
    use_range_filter: bool = True  # فقط در بازار رنج
    adx_max: float = 25.0  # ADX < 25 = رنج
    warmup_candles: int = 50

    # Reset conditions
    reset_after_hours: int = 24  # بعد از N ساعت، grid رو باز کن
