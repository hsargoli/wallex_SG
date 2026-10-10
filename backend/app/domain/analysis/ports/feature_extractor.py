"""FeatureExtractorPort — قرارداد استخراج feature از کندل‌ها."""

from __future__ import annotations

from typing import Protocol, Sequence

from app.domain.analysis.value_objects.feature_vector import FeatureVector
from app.domain.entities.candle import Candle


class FeatureExtractorPort(Protocol):
    """پیاده‌سازی‌ها: ta_features (خالص), external libs (future)."""

    def extract(self, candles: Sequence[Candle]) -> FeatureVector:
        """از یه پنجره‌ی کندل، یه FeatureVector بساز."""
        ...
