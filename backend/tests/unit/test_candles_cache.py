"""Test-first for CandlesCache + GetCandlesUseCase cache integration.

RED before wiring: TestGetCandlesUseCaseWithCache::test_second_call_uses_cache
will FAIL because use_case does not yet consult the cache (2 exchange calls
instead of 1).

GREEN after wiring (next block): all tests pass.
"""
from __future__ import annotations

import asyncio
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.domain.entities.candle import Candle
from app.infrastructure.cache.candles import CandlesCache, cache


def _c(t: int) -> Candle:
    return Candle(
        time=t,
        open=Decimal("100"),
        high=Decimal("110"),
        low=Decimal("90"),
        close=Decimal("105"),
        volume=Decimal("1"),
    )


# ─── CandlesCache (pure, no wiring needed — all GREEN from day 1) ───

class TestCandlesCacheClass:
    def test_get_empty_returns_none(self):
        c = CandlesCache()
        assert c.get("BTCTMN", "1h", 100) is None

    def test_set_then_get_returns_same(self):
        c = CandlesCache()
        data = [_c(1), _c(2)]
        c.set("BTCTMN", "1h", 100, data)
        assert c.get("BTCTMN", "1h", 100) == data

    def test_different_keys_isolated(self):
        c = CandlesCache()
        c.set("BTCTMN", "1h", 100, [_c(1)])
        c.set("ETHTMN", "1h", 100, [_c(2)])
        c.set("BTCTMN", "4h", 100, [_c(3)])
        c.set("BTCTMN", "1h", 200, [_c(4)])
        assert c.get("BTCTMN", "1h", 100)[0].time == 1
        assert c.get("ETHTMN", "1h", 100)[0].time == 2
        assert c.get("BTCTMN", "4h", 100)[0].time == 3
        assert c.get("BTCTMN", "1h", 200)[0].time == 4

    def test_ttl_expiry(self):
        fake_now = [1000.0]
        c = CandlesCache(ttl_seconds=10, clock=lambda: fake_now[0])
        c.set("BTCTMN", "1h", 100, [_c(1)])
        fake_now[0] = 1005.0  # 5s later — still valid
        assert c.get("BTCTMN", "1h", 100) is not None
        fake_now[0] = 1011.0  # 11s later — expired
        assert c.get("BTCTMN", "1h", 100) is None

    def test_clear(self):
        c = CandlesCache()
        c.set("BTCTMN", "1h", 100, [_c(1)])
        assert len(c) == 1
        c.clear()
        assert len(c) == 0
        assert c.get("BTCTMN", "1h", 100) is None


# ─── GetCandlesUseCase + cache wiring (RED until wired) ───

class TestGetCandlesUseCaseWithCache:
    @pytest.fixture(autouse=True)
    def _reset(self):
        cache.clear()
        yield
        cache.clear()

    def test_first_call_hits_exchange(self):
        from app.application.use_cases.get_candles import GetCandlesUseCase
        ex = MagicMock()
        ex.get_candles = AsyncMock(return_value=[_c(1), _c(2)])
        uc = GetCandlesUseCase(exchange=ex)
        result = asyncio.run(uc.execute("BTCTMN", "1h", 100))
        assert ex.get_candles.await_count == 1
        assert len(result) > 0

    def test_second_call_uses_cache(self):
        from app.application.use_cases.get_candles import GetCandlesUseCase
        ex = MagicMock()
        ex.get_candles = AsyncMock(return_value=[_c(1), _c(2)])
        uc = GetCandlesUseCase(exchange=ex)
        asyncio.run(uc.execute("BTCTMN", "1h", 100))
        asyncio.run(uc.execute("BTCTMN", "1h", 100))
        # RED until use_case consults the cache:
        # expected 1, without wiring will be 2
        assert ex.get_candles.await_count == 1

    def test_different_limit_misses_cache(self):
        from app.application.use_cases.get_candles import GetCandlesUseCase
        ex = MagicMock()
        ex.get_candles = AsyncMock(return_value=[_c(1)])
        uc = GetCandlesUseCase(exchange=ex)
        asyncio.run(uc.execute("BTCTMN", "1h", 100))
        asyncio.run(uc.execute("BTCTMN", "1h", 200))
        assert ex.get_candles.await_count == 2


class TestStaleFallback:
    """Stale fallback: if exchange fails, return expired cache instead of raising."""

    def test_get_stale_returns_expired_data(self):
        from app.infrastructure.cache.candles import CandlesCache
        fake_now = [1000.0]
        c = CandlesCache(ttl_seconds=10, clock=lambda: fake_now[0])
        c.set("BTCTMN", "1h", 100, [_c(1), _c(2)])
        fake_now[0] = 1005.0  # fresh
        assert c.get("BTCTMN", "1h", 100) is not None
        fake_now[0] = 1011.0  # expired
        assert c.get("BTCTMN", "1h", 100) is None
        # RED: get_stale doesn't exist yet
        assert c.get_stale("BTCTMN", "1h", 100) is not None
        assert len(c.get_stale("BTCTMN", "1h", 100)) == 2

    def test_get_stale_returns_none_when_never_cached(self):
        from app.infrastructure.cache.candles import CandlesCache
        c = CandlesCache()
        assert c.get_stale("BTCTMN", "1h", 100) is None

    def test_get_does_not_pop_expired(self):
        """After expiry, entry should remain as stale (not deleted)."""
        from app.infrastructure.cache.candles import CandlesCache
        fake_now = [1000.0]
        c = CandlesCache(ttl_seconds=10, clock=lambda: fake_now[0])
        c.set("BTCTMN", "1h", 100, [_c(1)])
        fake_now[0] = 1100.0  # expired
        c.get("BTCTMN", "1h", 100)  # returns None
        assert len(c) == 1  # entry still in store

    def test_use_case_returns_stale_on_exchange_failure(self):
        """RED: current code raises; new code returns stale."""
        from app.application.use_cases.get_candles import GetCandlesUseCase
        ex = MagicMock()
        ex.get_candles = AsyncMock(return_value=[_c(1), _c(2)])
        uc = GetCandlesUseCase(exchange=ex)
        asyncio.run(uc.execute("BTCTMN", "1h", 100))  # warm cache
        # Force-expire by shifting cache clock
        orig_clock = cache._clock
        cache._clock = lambda: orig_clock() + 10**6
        try:
            ex.get_candles = AsyncMock(side_effect=Exception("wallex down"))
            # RED today: raises. GREEN: returns stale 2 candles
            result = asyncio.run(uc.execute("BTCTMN", "1h", 100))
            assert len(result) == 2
        finally:
            cache._clock = orig_clock
            cache.clear()

    def test_use_case_raises_when_no_stale(self):
        """No stale data + exchange down → still raises (correct)."""
        from app.application.use_cases.get_candles import GetCandlesUseCase
        ex = MagicMock()
        ex.get_candles = AsyncMock(side_effect=Exception("wallex down"))
        uc = GetCandlesUseCase(exchange=ex)
        cache.clear()
        with pytest.raises(Exception):
            asyncio.run(uc.execute("NEWTMN", "1h", 100))

