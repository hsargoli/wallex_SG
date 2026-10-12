"""Executor — abstraction بین paper و live.

- PaperExecutor: فقط ثبت virtual، بدون API call
- LiveExecutor: سفارش واقعی روی Wallex
"""

from __future__ import annotations

import time
from decimal import Decimal
from typing import Protocol

import structlog

from app.domain.entities.order import (
    Order,
    OrderRequest,
    OrderSide,
    OrderStatus,
    OrderType,
)
from app.domain.ports.exchange import ExchangePort

log = structlog.get_logger("nooaah.executor")


class Executor(Protocol):
    """قرارداد اجرای سفارش."""

    async def place_market_buy(
        self, symbol: str, quantity: Decimal, client_id: str
    ) -> Order: ...

    async def get_current_price(self, symbol: str) -> float: ...


# ============================================================
# Paper Executor
# ============================================================
class PaperExecutor:
    """شبیه‌سازی: سفارش‌ها فقط ثبت می‌شوند، API صدا زده نمی‌شود.

    قیمت از ExchangePort گرفته می‌شود (live price).
    """

    def __init__(self, exchange: ExchangePort) -> None:
        self._exchange = exchange

    async def place_market_buy(
        self, symbol: str, quantity: Decimal, client_id: str
    ) -> Order:
        """ثبت virtual — فرض می‌کنیم همیشه fill می‌شود."""
        price = await self.get_current_price(symbol)
        log.info(
            "paper.fill",
            symbol=symbol,
            quantity=str(quantity),
            price=price,
            client_id=client_id,
        )
        return Order(
            client_id=client_id,
            symbol=symbol,
            side=OrderSide.BUY,
            type=OrderType.MARKET,
            quantity=quantity,
            price=Decimal(str(price)),
            status=OrderStatus.FILLED,
            active=False,
        )

    async def get_current_price(self, symbol: str) -> float:
        """قیمت لحظه‌ای از Wallex."""
        markets = await self._exchange.get_markets()
        for m in markets:
            if str(m.symbol) == symbol:
                if m.last_price is not None:
                    return float(m.last_price)
        raise ValueError(f"symbol not found: {symbol}")


# ============================================================
# Live Executor
# ============================================================
class LiveExecutor:
    """سفارش واقعی روی Wallex."""

    def __init__(self, exchange: ExchangePort) -> None:
        self._exchange = exchange

    async def place_market_buy(
        self, symbol: str, quantity: Decimal, client_id: str
    ) -> Order:
        """MARKET BUY روی Wallex."""
        req = OrderRequest(
            symbol=symbol,
            side=OrderSide.BUY,
            type=OrderType.MARKET,
            quantity=quantity,
            client_id=client_id,
        )
        log.warning(
            "live.place_order",
            symbol=symbol,
            quantity=str(quantity),
            client_id=client_id,
        )
        return await self._exchange.place_order(req)

    async def get_current_price(self, symbol: str) -> float:
        markets = await self._exchange.get_markets()
        for m in markets:
            if str(m.symbol) == symbol:
                if m.last_price is not None:
                    return float(m.last_price)
        raise ValueError(f"symbol not found: {symbol}")
