"""RegimeClassifierPort — قرارداد طبقه‌بندی regime.

دو پیاده‌سازی Phase 1:
  - rule_based_classifier (از regime_detector.py منتقل شده)
  - kmeans_classifier (جدید، داده‌محور)
"""

from __future__ import annotations

from typing import Protocol, Sequence

from app.domain.analysis.entities.regime import RegimeResult
from app.domain.analysis.value_objects.feature_vector import FeatureVector
from app.domain.entities.candle import Candle


class RegimeClassifierPort(Protocol):
    """قرارداد طبقه‌بندی regime بازار."""

    def classify(self, candles: Sequence[Candle]) -> RegimeResult:
        """از کندل‌ها، regime فعلی رو تشخیص بده."""
        ...


class FeatureBasedClassifierPort(Protocol):
    """قرارداد طبقه‌بندی بر اساس feature (برای KMeans)."""

    def classify_features(self, fv: FeatureVector) -> RegimeResult:
        """از یه FeatureVector، regime رو تشخیص بده."""
        ...
