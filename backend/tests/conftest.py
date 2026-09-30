from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services import budget_service as budget_service_module
from app.services.budget_service import BudgetService


@pytest.fixture
def fresh_budget_service():
    """یک نمونه‌ی تازه از BudgetService برای تست‌های واحد."""
    return BudgetService(initial_budget=Decimal("100000"))


@pytest.fixture(autouse=True)
def reset_global_budget_service():
    """
    قبل از هر تست، singleton سراسری رو به حالت اولیه ریست می‌کنه
    تا state بین تست‌ها نشت نکنه.
    """
    svc = budget_service_module.budget_service
    svc._allocated_budget = Decimal("100000")
    svc._in_use_capital = Decimal("0")
    yield
    # پاک‌سازی بعد از تست
    svc._allocated_budget = Decimal("100000")
    svc._in_use_capital = Decimal("0")


@pytest.fixture
def client():
    """TestClient برای تست اندپوینت‌ها."""
    return TestClient(app)
