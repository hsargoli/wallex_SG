"""FIFO Cost Basis — محاسبه‌ی قیمت خرید بر اساس الگوریتم FIFO.

Per ADR 0018.

الگوریتم:
- سفارش‌های FILLED/PARTIAL با executed_qty > 0 رو بر اساس زمان صعودی مرتب می‌کنیم
- صف خریدها: [{qty, unit_cost, ts}]
- هر SELL از ابتدای صف (قدیمی‌ترین) مصرف می‌کنه
- صف باقی‌مونده = position فعلی + میانگین موزون قیمت

Edge cases (per ADR 0018):
- BUY fee → اضافه به total_cost (unit_cost بالاتر)
- SELL fee → در PnL (درآمد خالص کمتر) — فعلاً فقط realized PnL
- سفارش CANCELLED/NEW → نادیده
- سفارش PARTIAL → با executed_qty واقعی
- SELL بیشتر از صف → has_unknown_history=True
- Dust (<1e-8) → صفر
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from app.domain.entities.order import Order
from app.domain.value_objects.order_enums import OrderSide, OrderStatus


DUST_THRESHOLD = Decimal("0.00000001")  # 1e-8


@dataclass(frozen=True)
class AssetCostBasis:
    """نتیجه‌ی FIFO برای یک asset."""

    symbol: str
    total_qty: Decimal       # مجموع مقدار در صف (قابل ردیابی)
    avg_cost: Decimal        # میانگین موزون قیمت خرید
    total_cost: Decimal      # total_qty * avg_cost
    has_unknown_history: bool


def _is_countable(order: Order) -> bool:
    """آیا این سفارش در محاسبه‌ی FIFO حساب می‌شه؟"""
    if order.executed_qty <= 0:
        return False
    return order.status in (OrderStatus.FILLED, OrderStatus.PARTIALLY_FILLED)


def compute_cost_basis(orders: list[Order]) -> dict[str, AssetCostBasis]:
    """محاسبه‌ی FIFO cost basis برای همه‌ی assetها.

    Args:
        orders: لیست سفارش‌ها (بدون ترتیب خاص)

    Returns:
        dict[symbol, AssetCostBasis] — فقط assetهایی که حداقل یک سفارش معتبر دارن
    """
    # ── 1. گروه‌بندی بر اساس symbol، فقط سفارش‌های معتبر ──
    by_symbol: dict[str, list[Order]] = {}
    for order in orders:
        if not _is_countable(order):
            continue
        by_symbol.setdefault(order.symbol, []).append(order)

    # ── 2. FIFO برای هر symbol ──
    result: dict[str, AssetCostBasis] = {}
    for symbol, symbol_orders in by_symbol.items():
        # مرتب‌سازی صعودی بر اساس created_at
        symbol_orders.sort(key=lambda o: o.created_at)

        # صف خریدها: هر آیتم {qty, unit_cost}
        queue: list[dict] = []
        has_unknown = False

        for order in symbol_orders:
            if order.side == OrderSide.BUY:
                # کارمزد خرید → هزینه‌ی بیشتر → unit_cost بالاتر
                total_cost = order.executed_sum + order.fee
                if order.executed_qty <= 0:
                    continue
                unit_cost = total_cost / order.executed_qty
                queue.append({
                    "qty": order.executed_qty,
                    "unit_cost": unit_cost,
                })

            elif order.side == OrderSide.SELL:
                remaining = order.executed_qty
                # مصرف FIFO از ابتدای صف
                while remaining > 0 and queue:
                    head = queue[0]
                    consumed = min(head["qty"], remaining)
                    head["qty"] -= consumed
                    remaining -= consumed
                    if head["qty"] <= 0:
                        queue.pop(0)
                # اگه چیزی مونده، یعنی فروش بیشتر از خریدهای شناخته‌شده
                if remaining > 0:
                    has_unknown = True

        # ── 3. محاسبه‌ی مجموع ──
        total_qty = sum(q["qty"] for q in queue)
        total_cost = sum(q["qty"] * q["unit_cost"] for q in queue)

        # Dust: خیلی کم → صفر
        if total_qty < DUST_THRESHOLD:
            total_qty = Decimal(0)
            total_cost = Decimal(0)

        avg_cost = total_cost / total_qty if total_qty > 0 else Decimal(0)

        result[symbol] = AssetCostBasis(
            symbol=symbol,
            total_qty=total_qty,
            avg_cost=avg_cost,
            total_cost=total_cost,
            has_unknown_history=has_unknown,
        )

    return result
