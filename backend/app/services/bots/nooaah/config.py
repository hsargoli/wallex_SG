"""تنظیمات ربات Nooaah."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class NooaahConfig:
    """تنظیمات پیش‌فرض Nooaah."""

    top_n: int = 5              # از بین چند نماد پرحجم انتخاب کن
    min_confidence: int = 60    # حداقل اطمینان برای ورود
    tp_atr_mult: float = 2.0    # TP = entry + 2×ATR
    sl_atr_mult: float = 1.0    # SL = entry − 1×ATR
    confirmation_candles: int = 1  # چند کندل متوالی trending_up برای ورود (1 = بدون confirmation)
    max_duration_hours: int = 24  # خروج بعد از ۲۴ کندل
    context_candles: int = 200  # context برای classifier
    min_candles: int = 100      # حداقل کندل برای تحلیل
