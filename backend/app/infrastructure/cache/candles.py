"""In-memory cache for Wallex candles.

Pattern mirrors _PNL_CACHE in services/wallex/service.py:309.
Server runs with workers=1, so in-memory is safe (per CTO decision 2026-10-24).

TTL is per timeframe: 15m candles change faster than 1D candles.
Key: (symbol, timeframe, limit) — different limit = different cache entry,
because the underlying fetch uses `limit` to size the request.
"""
from __future__ import annotations

import time
from typing import Callable

from app.domain.entities.candle import Candle

# TTL per timeframe (seconds)
DEFAULT_TTL: dict[str, int] = {
    "15m": 60,      # 1 min
    "1h": 300,      # 5 min
    "4h": 600,      # 10 min
    "1D": 3600,     # 1 hour
}
FALLBACK_TTL = 300


class CandlesCache:
    """Simple in-memory cache. Not thread-safe (single async event loop)."""

    def __init__(
        self,
        ttl_seconds: int | None = None,
        clock: Callable[[], float] | None = None,
    ) -> None:
        self._store: dict[tuple[str, str, int], tuple[float, list[Candle]]] = {}
        self._ttl_override = ttl_seconds
        self._clock = clock or time.time

    def _ttl_for(self, timeframe: str) -> int:
        if self._ttl_override is not None:
            return self._ttl_override
        return DEFAULT_TTL.get(timeframe, FALLBACK_TTL)

    def get(self, symbol: str, timeframe: str, limit: int) -> list[Candle] | None:
        key = (symbol, timeframe, limit)
        item = self._store.get(key)
        if item is None:
            return None
        ts, data = item
        if self._clock() - ts > self._ttl_for(timeframe):
            # Keep entry as stale (fallback via get_stale). Do NOT pop.
            return None
        return data

    def get_stale(self, symbol: str, timeframe: str, limit: int) -> list[Candle] | None:
        """Return cached data even if expired (stale-while-error fallback).

        Per CTO 2026-10-24: when wallex fails, serve last-known-good data
        instead of failing the request. Caller is responsible for using
        `get()` first (fresh) and `get_stale()` only on exchange failure.

        NOTE (tech debt): entries are never evicted (memory grows with
        symbol count, bounded in practice by ~400 symbols × small payloads).
        LRU eviction deferred post-MVP.
        """
        item = self._store.get((symbol, timeframe, limit))
        if item is None:
            return None
        return item[1]

    def set(self, symbol: str, timeframe: str, limit: int, candles: list[Candle]) -> None:
        self._store[(symbol, timeframe, limit)] = (self._clock(), candles)

    def clear(self) -> None:
        self._store.clear()

    def __len__(self) -> int:
        return len(self._store)


# module-level singleton (imported by GetCandlesUseCase)
cache = CandlesCache()
