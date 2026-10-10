"""تست rule_based و kmeans classifiers — با داده‌ی مصنوعی."""

from __future__ import annotations

from decimal import Decimal

import pytest

from app.domain.analysis.entities.regime import RegimeType
from app.domain.entities.candle import Candle
from app.infrastructure.analysis.kmeans_classifier import KMeansClassifier
from app.infrastructure.analysis.rule_based_classifier import RuleBasedClassifier


def make_uptrend(n: int = 150) -> list[Candle]:
    return [
        Candle(
            time=1000 + i * 3600,
            open=Decimal(str(100 + i * 0.5)),
            high=Decimal(str(101 + i * 0.5)),
            low=Decimal(str(99 + i * 0.5)),
            close=Decimal(str(100.4 + i * 0.5)),
            volume=Decimal(str(10 + (i % 5))),
        )
        for i in range(n)
    ]


def make_flat(n: int = 150) -> list[Candle]:
    return [
        Candle(
            time=1000 + i * 3600,
            open=Decimal("100"),
            high=Decimal("100.5"),
            low=Decimal("99.5"),
            close=Decimal("100"),
            volume=Decimal(str(10 + (i % 5))),
        )
        for i in range(n)
    ]


class TestRuleBasedClassifier:
    def test_insufficient_data_ranging(self) -> None:
        candles = make_flat(30)
        r = RuleBasedClassifier().classify(candles)
        assert r.regime == RegimeType.RANGING
        assert r.confidence == 0
        assert not r.is_tradeable

    def test_uptrend_detected(self) -> None:
        candles = make_uptrend(150)
        r = RuleBasedClassifier().classify(candles)
        assert r.regime == RegimeType.TRENDING_UP
        assert r.is_tradeable

    def test_flat_is_ranging(self) -> None:
        candles = make_flat(150)
        r = RuleBasedClassifier().classify(candles)
        assert r.regime == RegimeType.RANGING

    def test_reasons_not_empty(self) -> None:
        candles = make_uptrend(150)
        r = RuleBasedClassifier().classify(candles)
        assert len(r.reasons) > 0


class TestKMeansClassifier:
    def test_insufficient_data_no_model(self) -> None:
        cls = KMeansClassifier()
        cls.fit(make_flat(30))
        assert cls._model is None

    def test_fit_chooses_k(self) -> None:
        cls = KMeansClassifier(k_min=2, k_max=4)
        cls.fit(make_uptrend(200))
        assert cls._model is not None
        assert 2 <= cls._k <= 4

    def test_classify_without_fit_returns_default(self) -> None:
        cls = KMeansClassifier()
        r = cls.classify(make_uptrend(100))
        assert r.regime == RegimeType.RANGING
        assert r.confidence == 0

    def test_classify_after_fit(self) -> None:
        cls = KMeansClassifier(k_min=2, k_max=4)
        candles = make_uptrend(200)
        cls.fit(candles)
        r = cls.classify(candles)
        assert r.regime in (
            RegimeType.TRENDING_UP,
            RegimeType.TRENDING_DOWN,
            RegimeType.RANGING,
            RegimeType.CHOPPY,
        )
