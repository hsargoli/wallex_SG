"""TAFeatureExtractor — پیاده‌سازی FeatureExtractorPort با feature_math."""

from __future__ import annotations

from typing import Sequence

from app.domain.analysis.models.feature_math import extract_features
from app.domain.analysis.value_objects.feature_vector import FeatureVector
from app.domain.entities.candle import Candle


class TAFeatureExtractor:
    """Technical-analysis-based feature extractor (pure, no deps)."""

    def extract(self, candles: Sequence[Candle]) -> FeatureVector:
        return extract_features(candles)
