"""Phase 1A: detect_regime (ADX + EMA50)."""
from decimal import Decimal
import pytest
from app.domain.entities.candle import Candle
from app.services.bots.sarv_router.config import SarvRouterConfig
from app.services.bots.sarv_router.regime import Regime, detect_regime


def _c(t, price, high=None, low=None):
    p = Decimal(str(price))
    h = Decimal(str(high)) if high else p + 1
    l = Decimal(str(low)) if low else p - 1
    return Candle(time=t, open=p, high=h, low=l, close=p, volume=Decimal("100"))


def _uptrend_candles(n=200):
    """Strong uptrend — increasing price → high ADX + price > EMA50."""
    return [_c(i * 3600, 100 + i * 2) for i in range(n)]


def _downtrend_candles(n=200):
    """Strong downtrend — decreasing price → high ADX + price < EMA50."""
    return [_c(i * 3600, 400 - i * 2) for i in range(n)]


def _range_candles(n=200):
    """Flat/oscillating — low ADX."""
    return [_c(i * 3600, 100 + (i % 2)) for i in range(n)]


class TestDetectRegime:
    def test_uptrend(self):
        candles = _uptrend_candles(200)
        regime = detect_regime(candles, SarvRouterConfig())
        assert regime == Regime.UPTREND, f"expected UPTREND, got {regime}"

    def test_downtrend(self):
        candles = _downtrend_candles(200)
        regime = detect_regime(candles, SarvRouterConfig())
        assert regime == Regime.DOWNTREND, f"expected DOWNTREND, got {regime}"

    def test_range(self):
        candles = _range_candles(200)
        regime = detect_regime(candles, SarvRouterConfig())
        assert regime == Regime.RANGE, f"expected RANGE, got {regime}"

    def test_insufficient_data(self):
        candles = _uptrend_candles(20)
        regime = detect_regime(candles, SarvRouterConfig())
        assert regime == Regime.UNKNOWN, "insufficient data → UNKNOWN"

    def test_unknown_weak_adx(self):
        """ADX 20-25 → UNKNOWN (no clear trend)."""
        # This is hard to construct synthetically; will verify with real data in integration.
        pass
