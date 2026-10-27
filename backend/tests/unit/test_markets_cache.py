"""Test-first: MarketsCache must prevent duplicate Wallex calls within TTL."""
import asyncio
from unittest.mock import AsyncMock, MagicMock
import pytest
from app.application.use_cases.get_markets import GetMarketsUseCase
from app.infrastructure.cache.markets import cache

@pytest.fixture(autouse=True)
def _reset():
    cache.clear()
    yield
    cache.clear()

class TestMarketsCache:
    def test_markets_use_cache(self):
        ex = MagicMock()
        ex.get_markets = AsyncMock(return_value=["m1", "m2"])
        uc = GetMarketsUseCase(exchange=ex)
        
        # Call 1 (Cold)
        r1 = asyncio.run(uc.execute())
        assert r1 == ["m1", "m2"]
        assert ex.get_markets.await_count == 1
        
        # Call 2 (Warm)
        r2 = asyncio.run(uc.execute())
        assert r2 == ["m1", "m2"]
        assert ex.get_markets.await_count == 1  # Must still be 1
