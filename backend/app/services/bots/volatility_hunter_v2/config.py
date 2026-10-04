"""تنظیمات Volatility Hunter v2 — نسخه بهبودیافته.

فلسفه (ثابت با v1):
  - شکار نوسانات در محدوده
  - خرید در کف، فروش در سقف
  - خروج سریع

بهبودهای v2:
  - Percentile-based range (نه min/max)
  - فیلتر ADX برای تأیید رنج
  - فیلتر حجم
  - SL/TP بر مبنای ATR
  - تأیید ورود با RSI

نسخه بهینه‌شده (combined_4):
  - max_rsi = 55 (به جای 45)
  - min_volume_ratio = 0.5 (به جای 0.7)
  - buy_zone_pct = 20 (به جای 15)
  - tp_atr_mult = 4.0 (به جای 3.5)

نتایج بک‌تست 30 روز (5 نماد):
  - 32 معامله، WR=40.6%، PnL=+2.20%
  - (قبل از بهینه‌سازی: 23 معامله، WR=34.8%، PnL=+1.37%)
"""

from dataclasses import dataclass


@dataclass(slots=True)
class VolatilityHunterV2Config:
    """تنظیمات v2."""

    # --- عمومی ---
    timeframe: str = "1h"
    check_interval_sec: int = 300   # هر 5 دقیقه چک کن
    fee_pct: float = 0.2
    position_size_pct: float = 30.0  # 30% سرمایه در هر پوزیشن
    max_positions: int = 2

    # --- Range detection ---
    lookback_candles: int = 48        # 48 ساعت
    range_low_pct: float = 5.0        # صدک 5 = کف
    range_high_pct: float = 95.0      # صدک 95 = سقف

    # --- فیلترهای تأیید ---
    min_range_pct: float = 3.0        # حداقل دامنه
    max_range_pct: float = 15.0       # حداکثر (بالاتر = روند)
    min_atr_pct: float = 0.4          # حداقل نوسان
    max_adx: float = 25.0             # تأیید رنج (ADX پایین)
    min_volume_ratio: float = 0.5     # حجم نسبت به میانگین

    # --- ناحیه ورود ---
    buy_zone_pct: float = 20.0        # تا 15% بالای کف

    # --- تأیید ورود ---
    min_rsi: float = 20.0             # RSI در چه حداقل
    max_rsi: float = 55.0             # RSI در چه حداکثر (اشباع فروش)

    # --- ریسک ---
    sl_atr_mult: float = 2.0          # SL = entry - 2×ATR
    tp_atr_mult: float = 4.0          # TP = entry + 3.5×ATR
    trail_atr_mult: float = 1.5       # trailing stop پس از سود

    # --- محدودیت زمان ---
    max_duration_candles: int = 48    # حداکثر 48 ساعت
    warmup_candles: int = 100         # کندل‌های لازم برای شروع

    # --- Breakout ---
    breakout_pct: float = 3.0         # خروج اگه range شکست

