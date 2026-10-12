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

    async def place_market_sell(
        self, symbol: str, quantity: Decimal, client_id: str
    ) -> Order: ...

    async def get_current_price(self, symbol: str) -> float: ...

    async def get_best_bid(self, symbol: str) -> float: ...


def _fake_filled_order(
    client_id: str,
    symbol: str,
    side: OrderSide,
    quantity: Decimal,
    price: float,
) -> Order:
    """ساخت یه Order که کامل fill شده (برای paper)."""
    import time as _t
    now = int(_t.time())
    px = Decimal(str(price))
    return Order(
        client_id=client_id,
        symbol=symbol,
        side=side,
        type=OrderType.MARKET,
        status=OrderStatus.FILLED,
        price=px,
        stop_price=Decimal("0"),
        stop_price_condition="<=",
        orig_qty=quantity,
        executed_qty=quantity,
        executed_price=px,
        executed_sum=px * quantity,
        fee=Decimal("0"),
        active=False,
        executed_percent=Decimal("100"),
        created_at=now,
        updated_at=now,
    )


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
            "paper.fill_buy",
            symbol=symbol,
            quantity=str(quantity),
            price=price,
            client_id=client_id,
        )
        return _fake_filled_order(
            client_id, symbol, OrderSide.BUY, quantity, price
        )

    async def place_market_sell(
        self, symbol: str, quantity: Decimal, client_id: str
    ) -> Order:
        """ثبت virtual SELL — فرض می‌کنیم fill می‌شه با best_bid."""
        price = await self.get_best_bid(symbol)
        log.info(
            "paper.fill_sell",
            symbol=symbol,
            quantity=str(quantity),
            price=price,
            client_id=client_id,
        )
        return _fake_filled_order(
            client_id, symbol, OrderSide.SELL, quantity, price
        )

    async def get_current_price(self, symbol: str) -> float:
        """قیمت لحظه‌ای (آخرین معامله)."""
        markets = await self._exchange.get_markets()
        for m in markets:
            if str(m.symbol) == symbol:
                if m.last_price is not None:
                    return float(m.last_price)
        raise ValueError(f"symbol not found: {symbol}")

    async def get_best_bid(self, symbol: str) -> float:
        """بهترین قیمت خریدار (order book)."""
        from app.infrastructure.exchange.wallex.mapper import map_order_book
        try:
            raw = await self._exchange.get_order_book(symbol=symbol)
            book = map_order_book(raw, symbol=symbol)
            bb = getattr(book, "best_bid", None) or (
                book.get("best_bid") if isinstance(book, dict) else None
            )
            if bb:
                return float(bb)
        except Exception as exc:
            log.warning("get_best_bid_failed", symbol=symbol, error=str(exc))
        # fallback: last price
        return await self.get_current_price(symbol)


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

    async def place_market_sell(
        self, symbol: str, quantity: Decimal, client_id: str
    ) -> Order:
        """MARKET SELL روی Wallex."""
        req = OrderRequest(
            symbol=symbol,
            side=OrderSide.SELL,
            type=OrderType.MARKET,
            quantity=quantity,
            client_id=client_id,
        )
        log.warning(
            "live.place_sell",
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

    async def get_best_bid(self, symbol: str) -> float:
        from app.infrastructure.exchange.wallex.mapper import map_order_book
        try:
            raw = await self._exchange.get_order_book(symbol=symbol)
            book = map_order_book(raw, symbol=symbol)
            bb = getattr(book, "best_bid", None) or (
                book.get("best_bid") if isinstance(book, dict) else None
            )
            if bb:
                return float(bb)
        except Exception as exc:
            log.warning("get_best_bid_failed", symbol=symbol, error=str(exc))
        return await self.get_current_price(symbol)
