import threading
from decimal import Decimal


class InsufficientBotBudgetError(Exception):
    """Raised when an order exceeds the remaining free budget."""

    pass


class BudgetService:
    def __init__(self, initial_budget: Decimal = Decimal("0")):
        self._lock = threading.Lock()
        self._allocated_budget = initial_budget
        self._in_use_capital = Decimal("0")

    def set_budget(self, amount: Decimal) -> None:
        """Update bot total budget. Cannot be lower than currently used capital."""
        with self._lock:
            if amount < self._in_use_capital:
                raise ValueError(
                    f"New budget ({amount}) cannot be lower than "
                    f"capital currently in use ({self._in_use_capital})."
                )
            self._allocated_budget = amount

    def get_status(self) -> dict:
        with self._lock:
            available = max(Decimal("0"), self._allocated_budget - self._in_use_capital)
            return {
                "allocated_budget": self._allocated_budget,
                "in_use_capital": self._in_use_capital,
                "available_for_trade": available,
                "currency": "TMN",
            }

    def allocate_for_order(self, required_amount: Decimal) -> None:
        """Lock capital for a new buy order."""
        with self._lock:
            available = self._allocated_budget - self._in_use_capital
            if required_amount > available:
                raise InsufficientBotBudgetError(
                    f"Required: {required_amount}, Available: {available}"
                )
            self._in_use_capital += required_amount

    def release_capital(self, amount: Decimal) -> None:
        """Release locked capital when order is filled/canceled."""
        with self._lock:
            self._in_use_capital = max(Decimal("0"), self._in_use_capital - amount)


# Global singleton instance for the running application
budget_service = BudgetService(initial_budget=Decimal("100000"))  # Default 100k TMN safe guard
