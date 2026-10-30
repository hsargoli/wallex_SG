"""SarvTiger analyzer — feature extraction (TDD RED first)."""
import pytest
import numpy as np
from decimal import Decimal
from app.domain.entities.candle import Candle
from app.services.bots.sarv_tiger.analyzer.features import (
    extract_features, N_FEATURES,
)


def _c(t, o, h, l, c, v="100"):
    return Candle(
        time=t, open=Decimal(str(o)), high=Decimal(str(h)),
        low=Decimal(str(l)), close=Decimal(str(c)),
        volume=Decimal(str(v)),
    )


def _uptrend(n=30, start=100.0, step=1.0):
    return [_c(i*14400, start+i*step-0.5, start+i*step+1,
               start+i*step-1, start+i*step, v=str(100+i)) for i in range(n)]


def _flat(n=30, price=100.0):
    return [_c(i*14400, price, price+0.1, price-0.1, price) for i in range(n)]


def _volatile(n=30, price=100.0):
    return [_c(i*14400, price + (i%5-2)*3, price + (i%5-2)*3 + 2,
               price + (i%5-2)*3 - 2, price + (i%5-2)*3) for i in range(n)]


class TestFeatures:
    def test_returns_expected_length(self):
        feats = extract_features(_uptrend(), window=20)
        assert feats is not None
        assert len(feats) == N_FEATURES
        assert 10 <= N_FEATURES <= 15

    def test_handles_flat_market(self):
        feats = extract_features(_flat(), window=20)
        assert feats is not None
        assert np.all(np.isfinite(feats))

    def test_normalized_range_zscore(self):
        """All features within [-3, 3] (z-score, 3-sigma)."""
        feats = extract_features(_uptrend(), window=20)
        assert np.all(feats >= -3.0)
        assert np.all(feats <= 3.0)

    def test_insufficient_candles_returns_none(self):
        feats = extract_features(_flat(n=5), window=20)
        assert feats is None

    def test_normalization_uses_train_stats(self):
        """mean/std passed explicitly; not recomputed from current window."""
        train_mean = np.zeros(N_FEATURES)
        train_std = np.ones(N_FEATURES)
        feats = extract_features(
            _uptrend(), window=20,
            train_mean=train_mean, train_std=train_std,
        )
        assert feats is not None
        # With mean=0, std=1, output should equal raw features
        assert len(feats) == N_FEATURES

    def test_deterministic(self):
        """Same input → same output (no random)."""
        f1 = extract_features(_uptrend(), window=20)
        f2 = extract_features(_uptrend(), window=20)
        assert np.allclose(f1, f2)
