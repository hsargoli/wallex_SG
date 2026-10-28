"""تست AnalyzeSymbolUseCase — با mock exchange."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

import pytest

from app.application.use_cases.analyze_symbol import AnalyzeSymbolUseCase
from app.domain.entities.candle import Candle
from app.infrastructure.analysis.rule_based_classifier import RuleBasedClassifier
from app.infrastructure.cache.candles import cache as _candles_cache

import pytest

@pytest.fixture(autouse=True)
def clear_candles_cache():
    _candles_cache.clear()
    yield
    _candles_cache.clear()


class FakeExchange:
    """Exchange ماک — فقط get_candles."""

    def __init__(self, candles: list[Candle]) -> None:
        self._candles = candles

    async def get_candles(
        self, symbol: str, resolution: str, from_ts: int, to_ts: int
    ) -> list[Candle]:
        return self._candles


def make_candles(n: int) -> list[Candle]:
    return [
        Candle(
            time=1000 + i * 3600,
            open=Decimal(str(100 + i * 0.3)),
            high=Decimal(str(101 + i * 0.3)),
            low=Decimal(str(99 + i * 0.3)),
            close=Decimal(str(100.2 + i * 0.3)),
            volume=Decimal(str(10 + (i % 5))),
        )
        for i in range(n)
    ]


class TestAnalyzeSymbolUseCase:
    async def test_empty_candles_returns_zero(self) -> None:
        ex = FakeExchange([])
        uc = AnalyzeSymbolUseCase(exchange=ex, classifier=RuleBasedClassifier())
        stats = await uc.execute(symbol="BTCTMN", timeframe="1h")
        assert stats.window_count == 0
        assert stats.symbol == "BTCTMN"

    async def test_too_few_candles(self) -> None:
        ex = FakeExchange(make_candles(30))
        uc = AnalyzeSymbolUseCase(exchange=ex, classifier=RuleBasedClassifier())
        stats = await uc.execute(symbol="BTCTMN", timeframe="1h")
        assert stats.window_count == 0

    async def test_enough_candles_produces_stats(self) -> None:
        ex = FakeExchange(make_candles(300))
        uc = AnalyzeSymbolUseCase(exchange=ex, classifier=RuleBasedClassifier())
        stats = await uc.execute(symbol="BTCTMN", timeframe="1h")
        assert stats.window_count > 0
        assert stats.volatility_mean >= 0
        assert stats.rsi_mean > 0

    async def test_dominant_regime_set(self) -> None:
        ex = FakeExchange(make_candles(300))
        uc = AnalyzeSymbolUseCase(exchange=ex, classifier=RuleBasedClassifier())
        stats = await uc.execute(symbol="BTCTMN", timeframe="1h")
        assert stats.dominant_regime is not None
