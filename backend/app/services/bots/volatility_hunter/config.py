"""تنظیمات Volatility Hunter — نسخه بهینه‌شده.

پارامترهای بهینه بر اساس تست 64 ترکیب:
  - min_atr_pct: 1.0% (کمتر سختگیرانه)
  - min_range_pct: 7.0% (range کافی)
  - buy_zone_pct: 10.0% (نزدیک کف)

نتیجه:
  - بازده: +17.49%
  - DD: 4.41%
  - R/DD: 3.96 (بهترین ربات)
  - WR: 52.4%
"""

from dataclasses import dataclass


@dataclass(slots=True)
class VolatilityHunterConfig:
    """تنظیمات بهینه‌شده نوسان‌گیر."""

    timeframe: str = "1h"
    check_interval_sec: int = 300
    fee_pct: float = 0.2

    # تشخیص ولتیلیتی
    min_atr_pct: float = 1.0
    lookback_candles: int = 48

    # محدوده
    min_range_pct: float = 7.0
    max_range_pct: float = 30.0

    # سطوح ورود/خروج
    buy_zone_pct: float = 10.0
    sell_zone_pct: float = 10.0

    # ریسک
    breakout_pct: float = 3.0
    position_size_pct: float = 30.0
    max_positions: int = 3

    # TP/SL
    stop_loss_pct: float = 3.0
    take_profit_pct: float = 5.0

    warmup_candles: int = 100
