"""UseCase: میانگین وزنی قیمت خرید هر دارایی."""

from dataclasses import dataclass
from decimal import Decimal

from app.domain.entities.order import Order
from app.domain.ports import ExchangePort
from app.domain.value_objects.order_enums import OrderSide, OrderStatus


@dataclass(slots=True)
class CostBasisItem:
    """میانگین خرید برای یک نماد."""

    symbol: str
    avg_buy_price: Decimal
    total_qty_bought: Decimal
    total_invested: Decimal  # به ارز quote نماد
    orders_count: int
    buy_count: int
    sell_count: int


@dataclass(slots=True)
class GetCostBasisUseCase:
    exchange: ExchangePort

    async def execute(self) -> list[CostBasisItem]:
        """گروه‌بندی سفارش‌های BUY + FILLED و محاسبه میانگین وزنی."""
        orders = await self.exchange.get_orders()

        # فیلتر BUY + FILLED + executed_qty > 0 (برای میانگین)
        filled_buys: list[Order] = [
            o for o in orders
            if o.side == OrderSide.BUY
            and o.status == OrderStatus.FILLED
            and o.executed_qty > 0
        ]

        # شمارش SELL + FILLED (فقط برای نمایش تعداد)
        sell_counts: dict[str, int] = {}
        for o in orders:
            if (
                o.side == OrderSide.SELL
                and o.status == OrderStatus.FILLED
                and o.executed_qty > 0
            ):
                s = o.symbol.upper()
                sell_counts[s] = sell_counts.get(s, 0) + 1

        # گروه‌بندی بر اساس symbol
        grouped: dict[str, list[Order]] = {}
        for o in filled_buys:
            grouped.setdefault(o.symbol.upper(), []).append(o)

        result: list[CostBasisItem] = []
        for symbol, items in grouped.items():
            total_qty = sum((o.executed_qty for o in items), Decimal(0))
            if total_qty <= 0:
                continue
            total_sum = sum((o.executed_sum for o in items), Decimal(0))
            avg = total_sum / total_qty
            result.append(
                CostBasisItem(
                    symbol=symbol,
                    avg_buy_price=avg,
                    total_qty_bought=total_qty,
                    total_invested=total_sum,
                    orders_count=len(items),
                    buy_count=len(items),
                    sell_count=sell_counts.get(symbol, 0),
                )
            )

        # مرتب‌سازی بر اساس سرمایه
        result.sort(key=lambda x: x.total_invested, reverse=True)
        return result
