"""منطق خالص ربات تعقیب‌کننده‌ی سفارش (بدون I/O).

خرید: در بازه‌ی [low, high] سفارش Limit را در صدر خریدارها نگه دار، با یک tick بالاتر
از بهترین خریدار «دیگران» و هرگز بالاتر از high.
فروش: آینه‌ی همین. سفارش خودمان قبل از محاسبه از دفتر کم می‌شود تا خودمان را تعقیب نکنیم.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_CEILING, ROUND_FLOOR, Decimal
from enum import Enum

Level = tuple[Decimal, Decimal]  # (price, quantity)


class Action(str, Enum):
    WAIT = "WAIT"      # سفارشی نیست و فعلاً نباید گذاشت
    PLACE = "PLACE"    # سفارش جدید بگذار
    KEEP = "KEEP"      # سفارش فعلی خوب است
    MOVE = "MOVE"      # لغو و ثبت دوباره در قیمت جدید
    CANCEL = "CANCEL"  # سفارش فعلی را لغو کن و دوباره نگذار


@dataclass(frozen=True)
class Decision:
    action: Action
    price: Decimal | None
    reason: str


def _snap(price: Decimal, tick: Decimal, up: bool) -> Decimal:
    return (price / tick).to_integral_value(ROUND_CEILING if up else ROUND_FLOOR) * tick


def _without_own(levels: list[Level], own_price: Decimal | None, own_qty: Decimal) -> list[Level]:
    out: list[Level] = []
    for p, q in levels:
        if own_price is not None and p == own_price:
            q = q - own_qty
        if q > 0:
            out.append((p, q))
    return out


def decide(
    side: str,
    bids: list[Level],
    asks: list[Level],
    low: Decimal,
    high: Decimal,
    tick: Decimal,
    own_price: Decimal | None = None,
    own_qty: Decimal = Decimal(0),
    min_move_ticks: int = 1,
    enforce_bound: bool = False,
) -> Decision:
    """side: BUY یا SELL.

    enforce_bound: برای خرید یعنی «کف» را هم قید بدان و برای فروش یعنی «سقف» را.
    سقف خرید (high) و کف فروش (low) همیشه سخت هستند.
    """
    if tick <= 0:
        raise ValueError("tick باید مثبت باشد")
    if low > high:
        raise ValueError("کف بازه نباید از سقف بزرگ‌تر باشد")
    if side not in ("BUY", "SELL"):
        raise ValueError("side نامعتبر")

    bids = sorted(_without_own(bids, own_price if side == "BUY" else None, own_qty), key=lambda x: -x[0])
    asks = sorted(_without_own(asks, own_price if side == "SELL" else None, own_qty), key=lambda x: x[0])

    def finish(target: Decimal) -> Decision:
        if own_price is None:
            return Decision(Action.PLACE, target, "ثبت سفارش در صدر دفتر")
        if abs(target - own_price) < tick * min_move_ticks:
            return Decision(Action.KEEP, own_price, "سفارش در جای مناسب است")
        return Decision(Action.MOVE, target, f"جابه‌جایی {own_price} → {target}")

    if side == "BUY":
        if not bids or not asks:
            return (Decision(Action.KEEP, own_price, "فقط سفارش خودم در دفتر است")
                    if own_price is not None and asks
                    else Decision(Action.WAIT, None, "دفتر سفارش خالی است"))
        top, ask = bids[0][0], asks[0][0]
        if own_price is None and top > high:
            return Decision(Action.WAIT, None, "قیمت هنوز بالاتر از سقف بازه است")
        target = min(top + tick, high)
        if target >= ask:
            target = ask - tick
            if target <= top:
                target = top  # اسپرد یک tick است؛ کنار صدر می‌ایستیم
        target = min(_snap(target, tick, up=False), high)
        if enforce_bound and target < low:
            return (Decision(Action.CANCEL, None, "قیمت زیر کف بازه رفت")
                    if own_price is not None else Decision(Action.WAIT, None, "قیمت زیر کف بازه است"))
        return finish(target)

    # SELL
    if not bids or not asks:
        return (Decision(Action.KEEP, own_price, "فقط سفارش خودم در دفتر است")
                if own_price is not None and bids
                else Decision(Action.WAIT, None, "دفتر سفارش خالی است"))
    top, bid = asks[0][0], bids[0][0]
    if own_price is None and top < low:
        return Decision(Action.WAIT, None, "قیمت هنوز پایین‌تر از کف بازه است")
    target = max(top - tick, low)
    if target <= bid:
        target = bid + tick
        if target >= top:
            target = top  # اسپرد یک tick است؛ کنار صدر می‌ایستیم
    target = max(_snap(target, tick, up=True), low)
    if enforce_bound and target > high:
        return (Decision(Action.CANCEL, None, "قیمت بالای سقف بازه رفت")
                if own_price is not None else Decision(Action.WAIT, None, "قیمت بالای سقف بازه است"))
    return finish(target)
