"""Candle Aggregator — ادغام کندل‌های کوچک به بزرگ‌تر.

مثال:
    - ۱۵ کندل ۱ دقیقه‌ای → ۱ کندل ۱۵ دقیقه‌ای
    - ۴ کندل ۱ ساعته    → ۱ کندل ۴ ساعته
"""

from decimal import Decimal

from app.domain.entities.candle import Candle


def aggregate_candles(
    candles: list[Candle],
    factor: int,
) -> list[Candle]:
    """ادغام هر `factor` کندل متوالی به یک کندل بزرگ‌تر.

    Args:
        candles: لیست کندل‌های کوچک (مرتب‌شده بر اساس زمان صعودی)
        factor:  تعداد کندل‌هایی که باید ادغام شوند (مثلاً ۱۵ یا ۴)

    Returns:
        لیست کندل‌های ادغام‌شده

    منطق ادغام:
        - open  = open اولین کندل گروه
        - high  = بیشترین high بین گروه
        - low   = کمترین low بین گروه
        - close = close آخرین کندل گروه
        - volume = مجموع volume گروه
        - time  = زمان شروع اولین کندل گروه
    """
    if factor <= 1:
        return list(candles)
    if not candles:
        return []

    # مرتب‌سازی صعودی بر اساس زمان (مطمئن‌کاری)
    sorted_candles = sorted(candles, key=lambda c: c.time)

    result: list[Candle] = []
    for i in range(0, len(sorted_candles), factor):
        group = sorted_candles[i : i + factor]
        if not group:
            continue

        open_price = group[0].open
        close_price = group[-1].close
        high_price = max(c.high for c in group)
        low_price = min(c.low for c in group)
        total_volume = sum((c.volume for c in group), Decimal("0"))
        start_time = group[0].time

        result.append(
            Candle(
                time=start_time,
                open=open_price,
                high=high_price,
                low=low_price,
                close=close_price,
                volume=total_volume,
            )
        )

    return result
