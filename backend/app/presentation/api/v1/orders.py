"""Order endpoints — ثبت، لغو، لیست سفارش‌ها.

⚠️ امنیت:
    - ثبت و لغو سفارش فقط وقتی LIVE_TRADING_ENABLED=true فعاله
    - همه درخواست‌ها log میشن
    - Rate limiting اختصاصی برای هر endpoint
"""

import time

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status

from app.core.config import Settings, get_settings
from app.core.rate_limit import (
    CANCEL_ORDER_LIMIT,
    LIST_ORDERS_LIMIT,
    PLACE_ORDER_LIMIT,
    limiter,
)
from app.domain.entities.order import OrderRequest
from app.domain.exceptions import (
    ExchangeError,
    OrderNotFoundError,
    OrderRejectedError,
)
from app.domain.ports.exchange import ExchangePort
from app.domain.value_objects.order_enums import OrderSide, OrderType
from app.presentation.api.deps import get_user_exchange
from app.presentation.api.v1.schemas import (
    OrderListResponse,
    OrderResponse,
    PlaceOrderRequest,
)

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.get("/trading-mode")
async def trading_mode():
    """وضعیت قفل معامله‌ی واقعی (فقط می‌خواند؛ چیزی را تغییر نمی‌دهد)."""
    from app.core.config import Settings

    return {"live_enabled": bool(getattr(Settings(), "LIVE_TRADING_ENABLED", False)), "field": "LIVE_TRADING_ENABLED"}


def _require_live_trading(settings: Settings) -> None:
    """چک feature flag. اگه غیرفعاله، 403."""
    if not settings.can_trade:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "معامله واقعی غیرفعاله. "
                "برای فعال کردن، LIVE_TRADING_ENABLED=true در .env بگذارید."
            ),
        )


@router.post(
    "/place",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="ثبت سفارش جدید",
)
@limiter.limit(PLACE_ORDER_LIMIT)
async def place_order(
    request: Request,
    payload: PlaceOrderRequest,
    response: Response,
    exchange: ExchangePort = Depends(get_user_exchange),
    settings: Settings = Depends(get_settings),
) -> OrderResponse:
    """ثبت سفارش جدید.

    فقط وقتی LIVE_TRADING_ENABLED=true کار می‌کنه.
    محدودیت: ۵ درخواست در دقیقه.
    """
    _require_live_trading(settings)

    # client_id خودکار
    client_id = payload.client_id or f"api-{int(time.time())}-{payload.symbol[:3]}"

    try:
        order_request = OrderRequest(
            symbol=payload.symbol.upper(),
            side=OrderSide(payload.side),
            type=OrderType(payload.type),
            quantity=payload.quantity,
            price=payload.price,
            client_id=client_id,
            stop_price=payload.stop_price,
            stop_price_condition=payload.stop_price_condition,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    try:
        order = await exchange.place_order(order_request)
    except OrderRejectedError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ExchangeError as e:
        raise HTTPException(status_code=502, detail=str(e))

    return OrderResponse.from_entity(order)


@router.delete(
    "/cancel/{client_id}",
    response_model=OrderResponse,
    summary="لغو سفارش",
)
@limiter.limit(CANCEL_ORDER_LIMIT)
async def cancel_order(
    request: Request,
    response: Response,
    client_id: str,
    symbol: str = Query(..., description="نماد (مثل BTCTMN)"),
    exchange: ExchangePort = Depends(get_user_exchange),
    settings: Settings = Depends(get_settings),
) -> OrderResponse:
    """لغو سفارش با client_id. فقط وقتی LIVE_TRADING_ENABLED=true.

    محدودیت: ۱۰ درخواست در دقیقه.
    """
    _require_live_trading(settings)

    try:
        order = await exchange.cancel_order(client_id, symbol.upper())
    except OrderNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ExchangeError as e:
        raise HTTPException(status_code=502, detail=str(e))

    return OrderResponse.from_entity(order)


@router.get(
    "",
    response_model=OrderListResponse,
    summary="لیست سفارش‌ها",
)
@limiter.limit(LIST_ORDERS_LIMIT)
async def list_orders(
    request: Request,
    response: Response,
    symbol: str | None = Query(None, description="فیلتر بر اساس نماد"),
    status_filter: str | None = Query(
        None, alias="status", description="فیلتر وضعیت (NEW, FILLED, ...)"
    ),
    exchange: ExchangePort = Depends(get_user_exchange),
) -> OrderListResponse:
    """لیست سفارش‌های کاربر (read-only، safe).

    محدودیت: ۳۰ درخواست در دقیقه.
    """
    try:
        orders = await exchange.get_orders(
            symbol=symbol.upper() if symbol else None,
            status=status_filter,
        )
    except ExchangeError as e:
        raise HTTPException(status_code=502, detail=str(e))

    return OrderListResponse(
        count=len(orders),
        orders=[OrderResponse.from_entity(o) for o in orders],
    )


@router.get(
    "/open",
    response_model=OrderListResponse,
    summary="سفارش‌های باز فعلی",
)
@limiter.limit(LIST_ORDERS_LIMIT)
async def list_open_orders(
    request: Request,
    response: Response,
    symbol: str | None = Query(None, description="فیلتر بر اساس نماد"),
    exchange: ExchangePort = Depends(get_user_exchange),
) -> OrderListResponse:
    """سفارش‌های باز فعلی (شامل STOP_LIMIT و LIMIT).

    اینا سرمایه رو درگیر می‌کنن و می‌تونن لغو بشن.
    """
    try:
        orders = await exchange.get_open_orders(
            symbol=symbol.upper() if symbol else None,
        )
    except ExchangeError as e:
        raise HTTPException(status_code=502, detail=str(e))

    return OrderListResponse(
        count=len(orders),
        orders=[OrderResponse.from_entity(o) for o in orders],
    )
