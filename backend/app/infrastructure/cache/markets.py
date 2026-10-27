"""In-memory cache for Wallex markets.
CTO 2026-10-27: TTL=1h to prevent ArvanCloud 504 timeouts on /v1/markets.
Pattern mirrors candles.py.
"""
from __future__ import annotations
import time
from app.domain.entities.market import Market

DEFAULT_TTL = 3600  # 1 hour

class MarketsCache:
    def __init__(self, ttl_seconds: int = DEFAULT_TTL):
        self._store: list[Market] | None = None
        self._timestamp: float = 0.0
        self._ttl = ttl_seconds
        self._clock = time.time

    def get(self) -> list[Market] | None:
        if self._store is None:
            return None
        if self._clock() - self._timestamp > self._ttl:
            return None
        return self._store

    def set(self, markets: list[Market]) -> None:
        self._store = markets
        self._timestamp = self._clock()

    def clear(self) -> None:
        self._store = None
        self._timestamp = 0.0

cache = MarketsCache()
