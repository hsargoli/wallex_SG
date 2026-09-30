"""Candle — یک کندل OHLCV در یک تایم‌فریم مشخص."""

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class Candle:
    """یک کندل OHLCV.

    Attributes:
        time: زمان شروع کندل (Unix timestamp به ثانیه)
        open: قیمت باز شدن
        high: بالاترین قیمت
        low: پایین‌ترین قیمت
        close: قیمت بسته شدن
        volume: حجم معاملات در این بازه
    """

    time: int
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal
