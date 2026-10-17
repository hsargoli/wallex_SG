"""تست FIFO cost basis — منطق خالص، بدون I/O."""

from __future__ import annotations

from decimal import Decimal

import pytest

from app.domain.entities.order import Order
from app.domain.value_objects.order_enums import (
    OrderSide,
    OrderStatus,
    OrderType,
)
from app.services.wallex.cost_basis import (
    DUST_THRESHOLD,
    AssetCostBasis,
    compute_cost_basis,
)


def make_order(
    symbol: str,
    side: OrderSide,
    qty: str,
    price: str,
    fee: str = "0",
    ts: int = 1000,
    status: OrderStatus = OrderStatus.FILLED,
) -> Order:
    """ساخت Order تست با مقادیر ساده."""
    q = Decimal(qty)
    p = Decimal(price)
    f = Decimal(fee)
    return Order(
        client_id=f"TEST-{ts}-{side}-{qty}",
        symbol=symbol,
        side=side,
        type=OrderType.LIMIT,
        status=status,
        price=p,
        stop_price=Decimal("0"),
        stop_price_condition="",
        orig_qty=q,
        executed_qty=q,
        executed_price=p,
        executed_sum=q * p,
        fee=f,
        active=False,
        executed_percent=Decimal("100"),
        created_at=ts,
        updated_at=ts,
    )


class TestSimpleBuy:
    def test_single_buy(self) -> None:
        """یه خرید بدون فروش → position کامل."""
        orders = [make_order("PEPETMN", OrderSide.BUY, "100", "10")]
        result = compute_cost_basis(orders)

        assert "PEPETMN" in result
        cb = result["PEPETMN"]
        assert cb.total_qty == Decimal("100")
        assert cb.avg_cost == Decimal("10")
        assert cb.total_cost == Decimal("1000")
        assert cb.has_unknown_history is False

    def test_two_buys_weighted_avg(self) -> None:
        """دو خرید → میانگین موزون."""
        orders = [
            make_order("PEPETMN", OrderSide.BUY, "100", "10", ts=1000),
            make_order("PEPETMN", OrderSide.BUY, "100", "20", ts=2000),
        ]
        result = compute_cost_basis(orders)
        cb = result["PEPETMN"]

        assert cb.total_qty == Decimal("200")
        assert cb.avg_cost == Decimal("15")
        assert cb.total_cost == Decimal("3000")

    def test_buy_fee_increases_cost(self) -> None:
        """کارمزد خرید → unit_cost بالاتر."""
        orders = [
            make_order("PEPETMN", OrderSide.BUY, "100", "10", fee="10"),
        ]
        result = compute_cost_basis(orders)
        cb = result["PEPETMN"]

        # total_cost = 1000 + 10 = 1010
        assert cb.total_cost == Decimal("1010")
        assert cb.avg_cost == Decimal("10.10")


class TestFIFOConsumption:
    def test_fifo_vs_weighted_avg(self) -> None:
        """FIFO با Weighted Avg فرق داره — تست کنیم FIFO درسته."""
        # خرید 100 @ 10، خرید 100 @ 20، فروش 100
        # FIFO: اولی مصرف می‌شه → باقی: 100 @ 20
        # Weighted: میانگین 15 → باقی: 100 @ 15
        orders = [
            make_order("PEPETMN", OrderSide.BUY, "100", "10", ts=1000),
            make_order("PEPETMN", OrderSide.BUY, "100", "20", ts=2000),
            make_order("PEPETMN", OrderSide.SELL, "100", "25", ts=3000),
        ]
        result = compute_cost_basis(orders)
        cb = result["PEPETMN"]

        assert cb.total_qty == Decimal("100")
        assert cb.avg_cost == Decimal("20")  # FIFO، نه 15
        assert cb.total_cost == Decimal("2000")

    def test_sell_partial_from_first(self) -> None:
        """فروش جزئی → بخشی از خرید اول مصرف می‌شه."""
        orders = [
            make_order("PEPETMN", OrderSide.BUY, "100", "10", ts=1000),
            make_order("PEPETMN", OrderSide.BUY, "100", "20", ts=2000),
            make_order("PEPETMN", OrderSide.SELL, "50", "25", ts=3000),
        ]
        result = compute_cost_basis(orders)
        cb = result["PEPETMN"]

        assert cb.total_qty == Decimal("150")
        expected_avg = Decimal("2500") / Decimal("150")
        assert cb.avg_cost == expected_avg
        assert cb.has_unknown_history is False

    def test_sell_all(self) -> None:
        """فروش همه → position صفر."""
        orders = [
            make_order("PEPETMN", OrderSide.BUY, "100", "10", ts=1000),
            make_order("PEPETMN", OrderSide.SELL, "100", "25", ts=2000),
        ]
        result = compute_cost_basis(orders)
        cb = result["PEPETMN"]

        assert cb.total_qty == Decimal("0")
        assert cb.total_cost == Decimal("0")
        assert cb.avg_cost == Decimal("0")
        assert cb.has_unknown_history is False


class TestUnknownHistory:
    def test_sell_more_than_bought(self) -> None:
        """فروش بیشتر از خریدهای شناخته‌شده → unknown_history."""
        orders = [
            make_order("PEPETMN", OrderSide.BUY, "100", "10", ts=1000),
            make_order("PEPETMN", OrderSide.SELL, "150", "25", ts=2000),
        ]
        result = compute_cost_basis(orders)
        cb = result["PEPETMN"]

        assert cb.has_unknown_history is True
        assert cb.total_qty == Decimal("0")

    def test_sell_without_any_buy(self) -> None:
        """فروش بدون خرید → unknown."""
        orders = [
            make_order("PEPETMN", OrderSide.SELL, "100", "25", ts=1000),
        ]
        result = compute_cost_basis(orders)
        cb = result["PEPETMN"]

        assert cb.has_unknown_history is True
        assert cb.total_qty == Decimal("0")


class TestEdgeCases:
    def test_cancelled_order_ignored(self) -> None:
        """سفارش CANCELLED نادیده."""
        orders = [
            make_order("PEPETMN", OrderSide.BUY, "100", "10", ts=1000),
            make_order(
                "PEPETMN", OrderSide.BUY, "50", "15", ts=2000,
                status=OrderStatus.CANCELED,
            ),
        ]
        result = compute_cost_basis(orders)
        cb = result["PEPETMN"]

        assert cb.total_qty == Decimal("100")

    def test_partial_order_uses_executed_qty(self) -> None:
        """سفارش PARTIAL با executed_qty واقعی."""
        partial = Order(
            client_id="TEST-PARTIAL",
            symbol="PEPETMN",
            side=OrderSide.BUY,
            type=OrderType.LIMIT,
            status=OrderStatus.PARTIALLY_FILLED,
            price=Decimal("10"),
            stop_price=Decimal("0"),
            stop_price_condition="",
            orig_qty=Decimal("100"),
            executed_qty=Decimal("30"),
            executed_price=Decimal("10"),
            executed_sum=Decimal("300"),
            fee=Decimal("0"),
            active=True,
            executed_percent=Decimal("30"),
            created_at=1000,
            updated_at=1000,
        )
        result = compute_cost_basis([partial])
        cb = result["PEPETMN"]

        assert cb.total_qty == Decimal("30")
        assert cb.total_cost == Decimal("300")

    def test_dust_treated_as_zero(self) -> None:
        """مقدار خیلی کم → صفر."""
        orders = [
            make_order(
                "PEPETMN", OrderSide.BUY,
                str(DUST_THRESHOLD / Decimal("10")),
                "10",
            ),
        ]
        result = compute_cost_basis(orders)
        cb = result["PEPETMN"]

        assert cb.total_qty == Decimal("0")
        assert cb.total_cost == Decimal("0")

    def test_empty_orders(self) -> None:
        """لیست خالی → dict خالی."""
        assert compute_cost_basis([]) == {}

    def test_multiple_symbols(self) -> None:
        """چند symbol جدا محاسبه می‌شن."""
        orders = [
            make_order("PEPETMN", OrderSide.BUY, "100", "10", ts=1000),
            make_order("BTCTMN", OrderSide.BUY, "0.5", "100000", ts=2000),
        ]
        result = compute_cost_basis(orders)

        assert "PEPETMN" in result
        assert "BTCTMN" in result
        assert result["PEPETMN"].avg_cost == Decimal("10")
        assert result["BTCTMN"].avg_cost == Decimal("100000")
