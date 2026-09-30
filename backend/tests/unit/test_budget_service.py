from decimal import Decimal

import pytest

from app.services.budget_service import (
    BudgetService,
    InsufficientBotBudgetError,
)


class TestBudgetServiceInit:
    def test_default_init_is_zero(self):
        svc = BudgetService()
        status = svc.get_status()
        assert status["allocated_budget"] == Decimal("0")
        assert status["in_use_capital"] == Decimal("0")
        assert status["available_for_trade"] == Decimal("0")
        assert status["currency"] == "TMN"

    def test_init_with_budget(self):
        svc = BudgetService(initial_budget=Decimal("50000"))
        status = svc.get_status()
        assert status["allocated_budget"] == Decimal("50000")
        assert status["available_for_trade"] == Decimal("50000")


class TestSetBudget:
    def test_set_budget_valid(self, fresh_budget_service):
        fresh_budget_service.set_budget(Decimal("75000"))
        assert fresh_budget_service.get_status()["allocated_budget"] == Decimal("75000")

    def test_set_budget_lower_than_in_use_raises(self, fresh_budget_service):
        fresh_budget_service.allocate_for_order(Decimal("50000"))
        with pytest.raises(ValueError, match="cannot be lower than capital currently in use"):
            fresh_budget_service.set_budget(Decimal("30000"))

    def test_set_budget_equal_to_in_use_is_allowed(self, fresh_budget_service):
        fresh_budget_service.allocate_for_order(Decimal("50000"))
        fresh_budget_service.set_budget(Decimal("50000"))  # نباید خطا بده
        assert fresh_budget_service.get_status()["allocated_budget"] == Decimal("50000")


class TestAllocateForOrder:
    def test_allocate_within_available(self, fresh_budget_service):
        fresh_budget_service.allocate_for_order(Decimal("30000"))
        status = fresh_budget_service.get_status()
        assert status["in_use_capital"] == Decimal("30000")
        assert status["available_for_trade"] == Decimal("70000")

    def test_allocate_exact_available(self, fresh_budget_service):
        fresh_budget_service.allocate_for_order(Decimal("100000"))
        status = fresh_budget_service.get_status()
        assert status["in_use_capital"] == Decimal("100000")
        assert status["available_for_trade"] == Decimal("0")

    def test_allocate_more_than_available_raises(self, fresh_budget_service):
        with pytest.raises(InsufficientBotBudgetError, match="Required: 150000"):
            fresh_budget_service.allocate_for_order(Decimal("150000"))

    def test_multiple_allocations_accumulate(self, fresh_budget_service):
        fresh_budget_service.allocate_for_order(Decimal("20000"))
        fresh_budget_service.allocate_for_order(Decimal("30000"))
        assert fresh_budget_service.get_status()["in_use_capital"] == Decimal("50000")

    def test_allocate_zero_is_allowed(self, fresh_budget_service):
        fresh_budget_service.allocate_for_order(Decimal("0"))
        assert fresh_budget_service.get_status()["in_use_capital"] == Decimal("0")


class TestReleaseCapital:
    def test_release_partial(self, fresh_budget_service):
        fresh_budget_service.allocate_for_order(Decimal("50000"))
        fresh_budget_service.release_capital(Decimal("20000"))
        status = fresh_budget_service.get_status()
        assert status["in_use_capital"] == Decimal("30000")
        assert status["available_for_trade"] == Decimal("70000")

    def test_release_all(self, fresh_budget_service):
        fresh_budget_service.allocate_for_order(Decimal("50000"))
        fresh_budget_service.release_capital(Decimal("50000"))
        assert fresh_budget_service.get_status()["in_use_capital"] == Decimal("0")

    def test_release_more_than_in_use_clamps_to_zero(self, fresh_budget_service):
        fresh_budget_service.allocate_for_order(Decimal("10000"))
        fresh_budget_service.release_capital(Decimal("99999"))
        assert fresh_budget_service.get_status()["in_use_capital"] == Decimal("0")

    def test_release_when_nothing_in_use(self, fresh_budget_service):
        fresh_budget_service.release_capital(Decimal("5000"))
        assert fresh_budget_service.get_status()["in_use_capital"] == Decimal("0")


class TestDecimalPrecision:
    def test_decimal_precision_preserved(self, fresh_budget_service):
        fresh_budget_service.set_budget(Decimal("123456.789012345"))
        status = fresh_budget_service.get_status()
        assert status["allocated_budget"] == Decimal("123456.789012345")

    def test_decimal_arithmetic_no_float_errors(self, fresh_budget_service):
        # 0.1 + 0.2 با float میشه 0.30000000000000004، با Decimal باید دقیق باشه
        fresh_budget_service.set_budget(Decimal("100000"))
        fresh_budget_service.allocate_for_order(Decimal("0.1"))
        fresh_budget_service.allocate_for_order(Decimal("0.2"))
        assert fresh_budget_service.get_status()["in_use_capital"] == Decimal("0.3")


class TestFullLifecycle:
    def test_allocate_and_release_cycle(self, fresh_budget_service):
        # سناریوی واقعی: سه سفارش باز میشه، یکی بسته میشه
        fresh_budget_service.allocate_for_order(Decimal("10000"))
        fresh_budget_service.allocate_for_order(Decimal("25000"))
        fresh_budget_service.allocate_for_order(Decimal("15000"))
        assert fresh_budget_service.get_status()["in_use_capital"] == Decimal("50000")

        fresh_budget_service.release_capital(Decimal("25000"))
        status = fresh_budget_service.get_status()
        assert status["in_use_capital"] == Decimal("25000")
        assert status["available_for_trade"] == Decimal("75000")
