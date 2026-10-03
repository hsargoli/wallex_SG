"""ExchangePort — قرارداد انتزاعی با هر صرافی."""

from typing import Any, Protocol, runtime_checkable

from app.domain.entities.balance import Balance
from app.domain.entities.candle import Candle
from app.domain.entities.market import Market
from app.domain.entities.order import Order, OrderRequest


@runtime_checkable
class ExchangePort(Protocol):
    """پورت صرافی — فقط داده بازار و حساب برای MVP."""

    async def get_markets(self) -> list[Market]:
        """همه مارکت‌های فعال صرافی."""
        ...

    async def get_market(self, symbol: str) -> Market:
        """یک مارکت مشخص. اگر نباشد InvalidSymbolError."""
        ...

    async def get_balances(self) -> list[Balance]:
        """موجودی همه دارایی‌های کاربر."""
        ...

    async def get_order_book(self, symbol: str) -> dict[str, Any]:
        """دفتر سفارشات خام برای یک نماد."""
        ...

    async def get_candles(
        self,
        symbol: str,
        resolution: str,
        from_ts: int,
        to_ts: int,
    ) -> list[Candle]:
        """دریافت کندل‌های تاریخی OHLCV از صرافی."""
        ...

    async def health_check(self) -> bool:
        """آیا صرافی در دسترس است؟"""
        ...

    async def place_order(self, request: "OrderRequest") -> "Order":
        """ثبت سفارش جدید.

        Args:
            request: درخواست سفارش با همه پارامترهای لازم

        Returns:
            Order: سفارش ثبت‌شده با client_id و status

        Raises:
            OrderRejectedError: صرافی سفارش را رد کرد
            InsufficientBalanceError: موجودی کافی نیست
            ExchangeError: خطای عمومی صرافی
        """
        ...

    async def cancel_order(self, client_id: str, symbol: str) -> "Order":
        """لغو سفارش با client_id.

        Args:
            client_id: شناسه یکتای سفارش
            symbol: نماد (والکس برای cancel لازم داره)

        Returns:
            Order: سفارش لغو شده

        Raises:
            OrderNotFoundError: سفارش پیدا نشد
        """
        ...
