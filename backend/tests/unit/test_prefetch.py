"""Test-first for CandlePrefetcher.

CandlePrefetcher warms the candle cache for top-N symbols on a schedule.
Per CTO 2026-10-24: keep wallex load low (top_n=10, interval=5min, ~11% duty).

Design:
- _refresh_top() does one cycle: get_markets -> sort by volume -> top N
  -> for each, fetch 1h + 1D (via GetCandlesUseCase, which caches)
- run() loops: _refresh_top() -> sleep(interval) -> ...
- errors in one cycle must NOT crash the loop (log and continue)
"""
from __future__ import annotations

import asyncio
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.domain.entities.candle import Candle
from app.domain.entities.market import Market
from app.infrastructure.cache.candles import cache


def _mk_market(symbol: str, volume: str) -> Market:
    m = MagicMock(spec=Market)
    m.symbol = symbol
    stats = MagicMock()
    stats.daily_quote_volume = Decimal(volume)
    m.stats = stats
    return m


def _mk_candle(t: int) -> Candle:
    return Candle(
        time=t,
        open=Decimal("100"),
        high=Decimal("110"),
        low=Decimal("90"),
        close=Decimal("105"),
        volume=Decimal("1"),
    )


class TestCandlePrefetcher:

    @pytest.fixture(autouse=True)
    def _reset(self):
        cache.clear()
        yield
        cache.clear()

    def _mk(self, top_n: int = 10, interval_sec: int = 300):
        from app.services.prefetch import CandlePrefetcher
        exchange = MagicMock()
        exchange.get_markets = AsyncMock(return_value=[
            _mk_market("BTCTMN", "1000000"),
            _mk_market("ETHTMN", "500000"),
            _mk_market("XRPTMN", "100000"),
            _mk_market("LOWTMN", "1"),
        ])
        exchange.get_candles = AsyncMock(return_value=[_mk_candle(1), _mk_candle(2)])
        return CandlePrefetcher(
            exchange=exchange,
            top_n=top_n,
            interval_sec=interval_sec,
        ), exchange

    def test_refresh_top_picks_top_n_by_volume(self):
        p, ex = self._mk(top_n=2)
        asyncio.run(p._refresh_top())
        symbols = {k[0] for k in cache._store.keys()}
        assert symbols == {"BTCTMN", "ETHTMN"}, f"got {symbols}"
        assert "XRPTMN" not in symbols
        assert "LOWTMN" not in symbols

    def test_refresh_top_fetches_both_timeframes(self):
        p, ex = self._mk(top_n=1)
        asyncio.run(p._refresh_top())
        keys = {(k[0], k[1]) for k in cache._store.keys()}
        assert ("BTCTMN", "1h") in keys
        assert ("BTCTMN", "1D") in keys

    def test_refresh_top_handles_empty_markets(self):
        p, ex = self._mk(top_n=10)
        ex.get_markets = AsyncMock(return_value=[])
        asyncio.run(p._refresh_top())
        assert len(cache) == 0

    def test_refresh_top_continues_on_single_symbol_error(self):
        """If one symbol's fetch raises, others still complete; loop doesn't crash."""
        p, ex = self._mk(top_n=2)
        # BTCTMN succeeds twice (1h, 1D); ETHTMN raises on every call
        async def side(symbol, **kw):
            if symbol == "ETHTMN":
                raise Exception("wallex timeout")
            return [_mk_candle(1), _mk_candle(2)]
        ex.get_candles = AsyncMock(side_effect=side)
        asyncio.run(p._refresh_top())  # must NOT raise
        symbols = {k[0] for k in cache._store.keys()}
        assert "BTCTMN" in symbols
        assert "ETHTMN" not in symbols

    def test_refresh_top_sorts_by_volume_desc(self):
        """If top_n=1, only the highest-volume symbol is cached."""
        p, ex = self._mk(top_n=1)
        asyncio.run(p._refresh_top())
        symbols = {k[0] for k in cache._store.keys()}
        assert symbols == {"BTCTMN"}

    def test_refresh_top_uses_limit_31_for_1d(self):
        """1D uses limit=31 (minimum for change_1m which needs daily[-31])."""
        p, ex = self._mk(top_n=1)
        asyncio.run(p._refresh_top())
        keys = list(cache._store.keys())
        by_tf = {k[1]: k[2] for k in keys}
        assert by_tf["1h"] == 100, f"1h limit should be 100, got {by_tf.get('1h')}"
        assert by_tf["1D"] == 31, f"1D limit should be 31, got {by_tf.get('1D')}"

    def test_run_cancels_cleanly(self):
        p, ex = self._mk(top_n=1, interval_sec=10_000)
        async def scenario():
            task = asyncio.create_task(p.run())
            await asyncio.sleep(0.1)
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            return True
        assert asyncio.run(scenario()) is True
        assert len(cache) >= 1
