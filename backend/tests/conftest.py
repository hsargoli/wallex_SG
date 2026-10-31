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
    """TestClient با lifespan فعال.

    با استفاده از `with`، lifespan handler اجرا می‌شه و
    `app.state.exchange` ساخته میشه.
    """
    with TestClient(app) as c:
        yield c

# ═══════════════════════════════════════════════════════════════
# Candles cache reset — جلوگیری از test pollution
# (test_markets_price_public قیمت واقعی BTC را cache می‌کند،
#  و test_manual_order_persists با FakeExchange(price=100)
#  همان قیمت ۲۱ میلیارد را برمی‌گرداند → "سرمایه کافی نیست")
# ═══════════════════════════════════════════════════════════════


@pytest.fixture(autouse=True)
def _clear_candles_cache_between_tests():
    """هر تست با cache خالی شروع می‌شود."""
    from app.infrastructure.cache.candles import cache as _candles_cache
    _candles_cache._store.clear()
    yield
    _candles_cache._store.clear()


# ═══════════════════════════════════════════════════════════════
# Rate limiter reset — جلوگیری از 429 در تست‌های متوالی
# (CONNECT_LIMIT=5/hour، تست‌ها ۱۴ بار /connect می‌زنن)
# ═══════════════════════════════════════════════════════════════


@pytest.fixture(autouse=True)
def _reset_limiter_between_tests():
    """Reset slowapi in-memory storage before each test."""
    from app.core.rate_limit import limiter
    storage = getattr(limiter, "_storage", None)
    if storage is not None and hasattr(storage, "storage"):
        try:
            storage.storage.clear()
        except Exception:
            pass
    yield
