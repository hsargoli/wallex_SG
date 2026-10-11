"""تنظیمات ربات Nooaah."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class NooaahConfig:
    """تنظیمات پیش‌فرض Nooaah."""

    top_n: int = 5              # از بین چند نماد پرحجم انتخاب کن
    min_confidence: int = 85    # حداقل اطمینان برای ورود (بهینه: walk-forward + time machine)
    tp_atr_mult: float = 2.0    # TP = entry + 2×ATR
    sl_atr_mult: float = 1.0    # SL = entry − 1×ATR
    confirmation_candles: int = 1  # چند کندل متوالی trending_up برای ورود (1 = بدون confirmation)
    regime_filter_window: int = 20      # چند کندل اخیر رو بررسی کن (0 = off)
    regime_filter_min_ratio: float = 0.30  # حداقل نسبت trending_up
    momentum_exit_candles: int = 30    # پنجره‌ی 1m برای momentum exit (0 = off)
    momentum_red_ratio: float = 0.6    # نسبت کندل‌های قرمز برای exit
    volume_z_min: float = -0.5         # فیلتر: اگه volume_z < این → وارد نشو (بهینه: A2)
    cooldown_after_sl: int = 0         # B3: چند کندل بعد از SL صبر کن (0 = off)
    use_confidence_sizing: bool = False  # B1: حجم متناسب با confidence
    conf_sizing_low: int = 80          # آستانه‌ی پایین confidence
    conf_sizing_high: int = 95         # آستانه‌ی بالا confidence
    size_mult_low: float = 0.7         # حجم در conf_sizing_low
    size_mult_high: float = 1.5        # حجم در conf_sizing_high
    rsi_entry_max: float = 100.0       # فیلتر: اگه RSI > این → وارد نشو (100 = off)
    rsi_entry_min: float = 0.0         # فیلتر: اگه RSI < این → وارد نشو (0 = off)
    use_trailing: bool = False         # Trailing ATR (بدون TP)
    trailing_atr_mult: float = 1.5     # فاصله‌ی trailing از peak (× ATR)
    momentum_mode: str = "ratio"       # ratio | consecutive | cumulative
    momentum_consecutive: int = 4      # حداقل کندل قرمز متوالی (mode=consecutive)
    momentum_cumulative_pct: float = -0.3  # آستانه‌ی مجموع تغییرات (mode=cumulative)
    max_duration_hours: int = 24  # خروج بعد از ۲۴ کندل
    context_candles: int = 200  # context برای classifier
    min_candles: int = 100      # حداقل کندل برای تحلیل
