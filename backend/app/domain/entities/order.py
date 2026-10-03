"""Order — موجودیت سفارش معاملاتی.

دو نوع:
    - OrderRequest: چیزی که برای ثبت سفارش می‌فرستیم
    - Order: چیزی که از صرافی برمی‌گرده

هر دو immutable هستن (frozen dataclass) و از Decimal استفاده می‌کنن.
"""

from dataclasses import dataclass
from decimal import Decimal

from app.domain.value_objects.order_enums import OrderSide, OrderStatus, OrderType


@dataclass(frozen=True, slots=True)
class OrderRequest:
    """درخواست ثبت سفارش.

    Attributes:
        symbol: نماد معاملاتی (مثل BTCTMN)
        side: سمت سفارش (BUY/SELL)
        type: نوع سفارش (LIMIT/MARKET/...)
        quantity: مقدار در واحد ارز پایه
        price: قیمت واحد (فقط برای LIMIT/STOP_LIMIT)
        client_id: شناسه یکتای سفارش (خودمان می‌سازیم)
        stop_price: قیمت تریگر (فقط برای STOP_*)
    """

    symbol: str
    side: OrderSide
    type: OrderType
    quantity: Decimal
    price: Decimal | None = None
    client_id: str = ""
    stop_price: Decimal | None = None

    def __post_init__(self) -> None:
        if self.quantity <= 0:
            raise ValueError("quantity باید بزرگتر از صفر باشه")
        if self.type in (OrderType.LIMIT, OrderType.STOP_LIMIT):
            if self.price is None or self.price <= 0:
                raise ValueError(f"قیمت برای سفارش {self.type} الزامی و باید > 0 باشه")
        if self.type in (OrderType.STOP_LIMIT, OrderType.STOP_MARKET):
            if self.stop_price is None or self.stop_price <= 0:
                raise ValueError(f"stop_price برای سفارش {self.type} الزامی است")


@dataclass(frozen=True, slots=True)
class Order:
    """سفارش برگشتی از صرافی.

    Attributes:
        client_id: شناسه یکتای سفارش (برای cancel و detail)
        symbol: نماد معاملاتی
        side: سمت سفارش
        type: نوع سفارش
        status: وضعیت فعلی
        price: قیمت سفارش
        orig_qty: مقدار اصلی درخواست‌شده
        executed_qty: مقدار اجرا شده تا الان
        executed_price: میانگین قیمت اجرا
        executed_sum: مجموع مبلغ اجرا شده (به ارز quote)
        fee: کارمزد پرداخت‌شده
        active: آیا هنوز در دفتر سفارشات فعاله؟
        executed_percent: درصد اجرا (0-100)
        created_at: زمان ثبت (Unix timestamp)
        updated_at: زمان آخرین تغییر
    """

    client_id: str
    symbol: str
    side: OrderSide
    type: OrderType
    status: OrderStatus
    price: Decimal
    stop_price: Decimal
    stop_price_condition: str
    orig_qty: Decimal
    executed_qty: Decimal
    executed_price: Decimal
    executed_sum: Decimal
    fee: Decimal
    active: bool
    executed_percent: Decimal
    created_at: int
    updated_at: int

    @property
    def is_filled(self) -> bool:
        return self.status == OrderStatus.FILLED

    @property
    def is_canceled(self) -> bool:
        return self.status == OrderStatus.CANCELED

    @property
    def is_open(self) -> bool:
        """آیا هنوز در دفتر سفارشات بازه؟"""
        return self.active and self.status in (
            OrderStatus.NEW,
            OrderStatus.PARTIALLY_FILLED,
        )
