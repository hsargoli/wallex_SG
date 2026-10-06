"""تنظیمات Volatility Hunter — نسخه بهینه‌شده برای تایم‌فریم 1h.

پارامترهای بهینه بر اساس داده‌ی واقعی BTCUSDT در تایم‌فریم 1h:
  - میانگین range در 48 ساعت اخیر: ~4.35%
  - میانگین ATR%: ~0.52%

پارامترها:
  - min_range_pct: 3.0% (کمی کمتر از میانگین → فرصت معامله بیشتر)
  - max_range_pct: 12.0% (بالاتر از این یعنی بازار روندداره، نه رنج)
  - min_atr_pct: 0.35% (کمی کمتر از میانگین)
  - buy_zone_pct: 15% (نزدیک کف range)
"""

from dataclasses import dataclass


@dataclass(slots=True)
class VolatilityHunterConfig:
    """تنظیمات بهینه‌شده نوسان‌گیر برای تایم‌فریم 1h."""

    timeframe: str = "1h"
    check_interval_sec: int = 300
    fee_pct: float = 0.2

    # تشخیص ولتیلیتی (تنظیم‌شده برای 1h)
    min_atr_pct: float = 0.35
    lookback_candles: int = 48   # 48 ساعت = 2 روز

    # محدوده (تنظیم‌شده برای 1h)
    min_range_pct: float = 3.0
    max_range_pct: float = 12.0

    # سطوح ورود/خروج
    buy_zone_pct: float = 30.0
    sell_zone_pct: float = 15.0

    # ریسک
    breakout_pct: float = 3.0
    position_size_pct: float = 30.0
    max_positions: int = 3

    # TP/SL
    stop_loss_pct: float = 2.0
    take_profit_pct: float = 4.0

    warmup_candles: int = 100
