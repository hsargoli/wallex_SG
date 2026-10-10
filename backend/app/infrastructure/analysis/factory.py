"""Factory برای انتخاب classifier بر اساس config."""

from __future__ import annotations

from app.core.config import get_settings
from app.domain.analysis.ports.regime_classifier import RegimeClassifierPort
from app.infrastructure.analysis.kmeans_classifier import KMeansClassifier
from app.infrastructure.analysis.rule_based_classifier import RuleBasedClassifier


def build_classifier() -> RegimeClassifierPort:
    """بر اساس ANALYSIS_CLASSIFIER در env، یه classifier بساز."""
    settings = get_settings()
    name = settings.ANALYSIS_CLASSIFIER.lower()
    if name == "kmeans":
        return KMeansClassifier()
    return RuleBasedClassifier()
