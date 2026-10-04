"""مدیریت بودجه‌ی ربات‌ها — پشتیبانی از تخصیص per-bot.

تغییرات نسخه ۲:
  - هر ربات می‌تونه تخصیص اختصاصی داشته باشه (allocated)
  - هر ربات سرمایه‌ی در گردش خودش رو داره (in_use)
  - مجموع تخصیص‌ها نباید از بودجه‌ی کل بیشتر بشه
  - بودجه‌ی کل = مجموع تخصیص‌ها + آزاد
"""

import threading
from decimal import Decimal


class InsufficientBotBudgetError(Exception):
    """سفارش از بودجه‌ی آزاد ربات بیشتره."""
    pass


class BudgetService:
    def __init__(self, initial_budget: Decimal = Decimal("0")):
        self._lock = threading.Lock()
        self._total_budget = initial_budget
        self._bot_allocations: dict[str, Decimal] = {}   # slug → allocated
        self._bot_in_use: dict[str, Decimal] = {}        # slug → in_use

    # ------------------------------------------------------------
    # Helpers (داخلی)
    # ------------------------------------------------------------
    @property
    def _total_allocated(self) -> Decimal:
        """مجموع تخصیص‌ها به ربات‌ها."""
        return sum(self._bot_allocations.values(), Decimal("0"))

    @property
    def _total_in_use(self) -> Decimal:
        """مجموع سرمایه‌ی در گردش همه‌ی ربات‌ها."""
        return sum(self._bot_in_use.values(), Decimal("0"))

    # ------------------------------------------------------------
    # بودجه‌ی کل
    # ------------------------------------------------------------
    def set_budget(self, amount: Decimal) -> None:
        """تعیین بودجه‌ی کل.

        نباید کمتر از مجموع تخصیص‌ها یا سرمایه‌ی در گردش باشه.
        """
        with self._lock:
            total_in_use = self._total_in_use
            if amount < total_in_use:
                raise ValueError(
                    f"New budget ({amount}) cannot be lower than "
                    f"capital currently in use ({total_in_use})."
                )
            if amount < self._total_allocated:
                raise ValueError(
                    f"New budget ({amount}) cannot be lower than "
                    f"total allocations to bots ({self._total_allocated})."
                )
            self._total_budget = amount

    def get_status(self) -> dict:
        """وضعیت کلی بودجه (دید بالا-به-پایین)."""
        with self._lock:
            total_allocated = self._total_allocated
            total_in_use = self._total_in_use
            unallocated = self._total_budget - total_allocated
            available = max(Decimal("0"), self._total_budget - total_in_use)

            return {
                "total_budget": self._total_budget,
                "total_allocated": total_allocated,
                "unallocated": unallocated,
                "total_in_use": total_in_use,
                "available": available,
                # سازگاری با کد قبلی
                "allocated_budget": self._total_budget,
                "in_use_capital": total_in_use,
                "available_for_trade": available,
                "currency": "TMN",
            }

    # ------------------------------------------------------------
    # بودجه‌ی هر ربات
    # ------------------------------------------------------------
    def set_bot_allocation(self, slug: str, amount: Decimal) -> None:
        """تعیین/به‌روزرسانی بودجه‌ی اختصاصی یک ربات.

        Raises:
            ValueError: اگه مجموع تخصیص‌ها از بودجه‌ی کل بیشتر بشه
            ValueError: اگه amount کمتر از in_use فعلی ربات باشه
        """
        with self._lock:
            if amount < 0:
                raise ValueError("مقدار بودجه نمی‌تونه منفی باشه.")

            current_in_use = self._bot_in_use.get(slug, Decimal("0"))
            if amount < current_in_use:
                raise ValueError(
                    f"بودجه‌ی {slug} ({amount}) نمی‌تونه کمتر از "
                    f"سرمایه‌ی در گردش فعلی ({current_in_use}) باشه."
                )

            # چک: مجموع تخصیص‌ها نباید از بودجه‌ی کل بیشتر بشه
            old_allocation = self._bot_allocations.get(slug, Decimal("0"))
            delta = amount - old_allocation
            new_total = self._total_allocated + delta
            if new_total > self._total_budget:
                raise ValueError(
                    f"مجموع تخصیص‌ها ({new_total}) از بودجه‌ی کل "
                    f"({self._total_budget}) بیشتر می‌شه. "
                    f"حداکثر برای این ربات: {old_allocation + (self._total_budget - self._total_allocated)}"
                )

            self._bot_allocations[slug] = amount

    def get_bot_status(self, slug: str) -> dict:
        """وضعیت بودجه‌ی یک ربات."""
        with self._lock:
            allocated = self._bot_allocations.get(slug, Decimal("0"))
            in_use = self._bot_in_use.get(slug, Decimal("0"))
            free = max(Decimal("0"), allocated - in_use)
            usage_pct = float(in_use / allocated * 100) if allocated > 0 else 0.0

            return {
                "slug": slug,
                "allocated": allocated,
                "in_use": in_use,
                "free": free,
                "usage_pct": round(usage_pct, 2),
                "currency": "TMN",
            }

    def list_bot_allocations(self) -> list[dict]:
        """لیست همه‌ی تخصیص‌ها."""
        with self._lock:
            # همه‌ی ربات‌های دارای تخصیص یا در گردش
            slugs = set(self._bot_allocations.keys()) | set(self._bot_in_use.keys())
            result = []
            for slug in sorted(slugs):
                allocated = self._bot_allocations.get(slug, Decimal("0"))
                in_use = self._bot_in_use.get(slug, Decimal("0"))
                free = max(Decimal("0"), allocated - in_use)
                usage_pct = float(in_use / allocated * 100) if allocated > 0 else 0.0
                result.append({
                    "slug": slug,
                    "allocated": allocated,
                    "in_use": in_use,
                    "free": free,
                    "usage_pct": round(usage_pct, 2),
                    "currency": "TMN",
                })
            return result

    # ------------------------------------------------------------
    # قفل/آزادسازی سرمایه
    # ------------------------------------------------------------
    def allocate_for_order(
        self,
        required_amount: Decimal,
        slug: str | None = None,
    ) -> None:
        """قفل کردن سرمایه برای یه خرید جدید.

        Args:
            required_amount: مبلغ لازم
            slug: اگه مشخص باشه، از بودجه‌ی همون ربات کم میشه.
                  در غیر این صورت، از بودجه‌ی کل (رفتار قدیمی).
        """
        with self._lock:
            if slug is None:
                # رفتار قدیمی
                available = self._total_budget - self._total_in_use
                if required_amount > available:
                    raise InsufficientBotBudgetError(
                        f"Required: {required_amount}, Available: {available}"
                    )
                # به یه slug خاص نسبت نمیدیم
                self._bot_in_use["__unassigned__"] = (
                    self._bot_in_use.get("__unassigned__", Decimal("0")) + required_amount
                )
                return

            allocated = self._bot_allocations.get(slug, Decimal("0"))
            in_use = self._bot_in_use.get(slug, Decimal("0"))
            available = allocated - in_use

            if required_amount > available:
                raise InsufficientBotBudgetError(
                    f"ربات {slug}: نیاز {required_amount}، آزاد {available}"
                )
            self._bot_in_use[slug] = in_use + required_amount

    def release_capital(
        self,
        amount: Decimal,
        slug: str | None = None,
    ) -> None:
        """آزادسازی سرمایه وقتی سفارش پر/لغو شد."""
        with self._lock:
            if slug is None:
                # رفتار قدیمی
                key = "__unassigned__"
            else:
                key = slug

            current = self._bot_in_use.get(key, Decimal("0"))
            self._bot_in_use[key] = max(Decimal("0"), current - amount)

    # ------------------------------------------------------------
    # Reset (برای تست)
    # ------------------------------------------------------------
    def reset(self) -> None:
        with self._lock:
            self._bot_allocations.clear()
            self._bot_in_use.clear()


# Global singleton
budget_service = BudgetService(initial_budget=Decimal("100000"))
