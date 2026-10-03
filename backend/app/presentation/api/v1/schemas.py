from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


# --- Market Schemas ---
class MarketOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    symbol: str
    base_asset: str
    quote_asset: str
    last_price: Decimal | None = None
    fa_name: str | None = None
    en_name: str | None = None
    daily_volume: Decimal | None = None
    daily_quote_volume: Decimal | None = None
    daily_change_percent: Decimal | None = None


class MarketsResponse(BaseModel):
    count: int
    items: list[MarketOut]


# --- Account Schemas ---
class BalanceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    asset: str
    available: Decimal
    locked: Decimal
    total: Decimal
    fa_name: str | None = None
    en_name: str | None = None


class BalancesResponse(BaseModel):
    count: int
    items: list[BalanceOut]


class KeyBalancesResponse(BaseModel):
    tmn_available: Decimal
    tmn_locked: Decimal
    usdt_available: Decimal
    usdt_locked: Decimal
    xrp_available: Decimal
    xrp_locked: Decimal


class OrderBookLevel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    price: Decimal
    quantity: Decimal
    sum: Decimal | None = None


class OrderBookResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    symbol: str
    best_bid: Decimal | None = None
    best_ask: Decimal | None = None
    spread: Decimal | None = None
    spread_pct: Decimal | None = None
    bids: list[OrderBookLevel] = []
    asks: list[OrderBookLevel] = []


class PortfolioItemOut(BaseModel):
    asset: str
    fa_name: str | None = None
    available: Decimal
    locked: Decimal
    total: Decimal

    price_usdt_bid: Decimal | None = None
    price_usdt_last: Decimal | None = None
    price_tmn_bid: Decimal | None = None
    price_tmn_last: Decimal | None = None

    value_usdt_bid: Decimal | None = None
    value_usdt_last: Decimal | None = None
    value_tmn_bid: Decimal | None = None
    value_tmn_last: Decimal | None = None

    share_pct_bid: Decimal = Decimal("0")
    share_pct_last: Decimal = Decimal("0")

    has_tmn_pair: bool = False
    has_usdt_pair: bool = False


class PortfolioResponse(BaseModel):
    count: int
    total_value_tmn_bid: Decimal
    total_value_tmn_last: Decimal
    total_value_usdt_bid: Decimal
    total_value_usdt_last: Decimal
    usdt_tmn_rate: Decimal | None = None
    items: list[PortfolioItemOut]


# ---------- Order Schemas ----------


class PlaceOrderRequest(BaseModel):
    """درخواست ثبت سفارش."""

    symbol: str = Field(..., min_length=3, max_length=20, description="نماد (مثل BTCTMN)")
    side: Literal["BUY", "SELL"] = Field(..., description="سمت سفارش")
    type: Literal["LIMIT", "MARKET", "STOP_LIMIT", "STOP_MARKET"] = Field(
        ..., description="نوع سفارش"
    )
    quantity: Decimal = Field(..., gt=0, description="مقدار در واحد ارز پایه")
    price: Decimal | None = Field(
        None, gt=0, description="قیمت (برای LIMIT و STOP_LIMIT الزامی)"
    )
    stop_price: Decimal | None = Field(
        None, gt=0, description="قیمت تریگر (برای STOP_* الزامی)"
    )
    stop_price_condition: Literal["<=", ">="] = Field(
        "<=", description="شرط فعال‌سازی STOP (فقط برای STOP_*)"
    )
    client_id: str | None = Field(
        None,
        max_length=40,
        pattern=r"^[A-Za-z0-9_]+$",
        description="شناسه یکتا (اختیاری — اگه ندید، خودکار ساخته میشه)",
    )


class OrderResponse(BaseModel):
    """پاسخ سفارش."""

    client_id: str
    symbol: str
    side: str
    type: str
    status: str
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

    @classmethod
    def from_entity(cls, order) -> "OrderResponse":
        return cls(
            client_id=order.client_id,
            symbol=order.symbol,
            side=order.side.value,
            type=order.type.value,
            status=order.status.value,
            price=order.price,
            stop_price=order.stop_price,
            stop_price_condition=order.stop_price_condition,
            orig_qty=order.orig_qty,
            executed_qty=order.executed_qty,
            executed_price=order.executed_price,
            executed_sum=order.executed_sum,
            fee=order.fee,
            active=order.active,
            executed_percent=order.executed_percent,
            created_at=order.created_at,
            updated_at=order.updated_at,
        )


class OrderListResponse(BaseModel):
    """لیست سفارش‌ها."""

    count: int
    orders: list[OrderResponse]
