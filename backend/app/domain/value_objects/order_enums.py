"""Enums مربوط به سفارش‌های معاملاتی.

مستقل از هر فریمورک یا صرافی خاص. مقادیر مطابق API والکس هستن.
"""

from enum import StrEnum


class OrderSide(StrEnum):
    """سمت سفارش."""

    BUY = "BUY"
    SELL = "SELL"


class OrderType(StrEnum):
    """نوع سفارش."""

    LIMIT = "LIMIT"
    MARKET = "MARKET"
    STOP_LIMIT = "STOP_LIMIT"
    STOP_MARKET = "STOP_MARKET"


class OrderStatus(StrEnum):
    """وضعیت سفارش.

    مقادیر ممکن بر اساس API والکس:
        NEW               → ثبت شده، منتظر اجرا
        PARTIALLY_FILLED  → بخشی اجرا شده
        FILLED            → کامل اجرا شده
        CANCELED          → لغو شده
        REJECTED          → رد شده توسط صرافی
        EXPIRED           → منقضی شده
    """

    NEW = "NEW"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    CANCELED = "CANCELED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"
    UNKNOWN = "UNKNOWN"  # برای مقادیر ناشناخته از API

    @classmethod
    def from_raw(cls, raw: str | None) -> "OrderStatus":
        """تبدیل رشته خام API به enum. مقدار ناشناخته → UNKNOWN."""
        if not raw:
            return cls.UNKNOWN
        try:
            return cls(raw.upper())
        except ValueError:
            return cls.UNKNOWN
