"""تنظیمات Grid Bot — نسخه بهینه‌شده.

پارامترها بر اساس بهینه‌سازی 60 ترکیب روی 8 نماد:
  - cash_pct: 25% → بهترین R/DD
  - spacing: 0.6×ATR → تنگ‌تر برای ترید بیشتر  
  - escape: 5% → نقطه‌ی طلایی
  - ADX max: 25 → فقط رنج

نتیجه Backtest:
  - بازده: +8.94%
  - DD: 8.92%
  - WR: 90.4%
  - R/DD: 1.00
"""

from dataclasses import dataclass


@dataclass(slots=True)
class GridBotConfig:
    """تنظیمات بهینه‌شده Grid Bot."""
    timeframe: str = "1h"
    check_interval_sec: int = 300
    fee_pct: float = 0.2

    # Grid levels
    n_buy_levels: int = 3
    n_sell_levels: int = 3          # هر buy یه sell متناظر
    grid_spacing_atr: float = 0.6   # ← بهینه
    cash_per_level_pct: float = 25.0  # ← بهینه

    # Detection
    adx_max: float = 25.0
    warmup_candles: int = 100

    # Risk management
    escape_pct: float = 5.0          # ← بهینه
    timeout_candles: int = 100
    max_exposure_pct: float = 60.0   # سقف سرمایه درگیر

    # Reset
    reset_after_hours: int = 72      # 3 روز
