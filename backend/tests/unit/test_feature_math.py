"""تست feature_math — منطق خالص."""

from __future__ import annotations

from decimal import Decimal

import pytest

from app.domain.analysis.models.feature_math import (
    adx,
    atr_last,
    ema_last,
    extract_features,
    rsi,
    trend_strength,
    volatility,
    volume_z,
)
from app.domain.entities.candle import Candle


def make_candles(closes: list[float], volume: float = 10.0) -> list[Candle]:
    """از لیست close، کندل بساز."""
    return [
        Candle(
            time=1000 + i * 3600,
            open=Decimal(str(c)),
            high=Decimal(str(c * 1.01)),
            low=Decimal(str(c * 0.99)),
            close=Decimal(str(c)),
            volume=Decimal(str(volume + i * 0.1)),
        )
        for i, c in enumerate(closes)
    ]


class TestVolatility:
    def test_constant_returns_zero(self) -> None:
        candles = make_candles([100.0] * 20)
        assert volatility(candles) == 0.0

    def test_uptrend_positive(self) -> None:
        candles = make_candles([100 + i for i in range(20)])
        assert volatility(candles) > 0


class TestRSI:
    def test_uptrend_near_100(self) -> None:
        candles = make_candles([100 + i for i in range(20)])
        assert rsi(candles) > 90

    def test_downtrend_near_zero(self) -> None:
        candles = make_candles([100 - i for i in range(20)])
        assert rsi(candles) < 10

    def test_insufficient_data_returns_50(self) -> None:
        candles = make_candles([100, 101])
        assert rsi(candles) == 50.0


class TestTrendStrength:
    def test_uptrend_positive(self) -> None:
        candles = make_candles([100 + i for i in range(30)])
        assert trend_strength(candles) > 0

    def test_downtrend_negative(self) -> None:
        candles = make_candles([100 - i for i in range(30)])
        assert trend_strength(candles) < 0


class TestVolumeZ:
    def test_last_spike_positive(self) -> None:
        candles = make_candles([100.0] * 20, volume=10.0)
        # آخرین کندل حجم بالا
        candles[-1] = Candle(
            time=candles[-1].time,
            open=candles[-1].open,
            high=candles[-1].high,
            low=candles[-1].low,
            close=candles[-1].close,
            volume=Decimal("1000"),
        )
        assert volume_z(candles) > 2


class TestADX:
    def test_strong_trend_high(self) -> None:
        # روند قوی صعودی
        candles = make_candles([100 + i * 2 for i in range(60)])
        a = adx(candles, 14)
        assert a > 20

    def test_flat_low(self) -> None:
        candles = make_candles([100.0] * 60)
        a = adx(candles, 14)
        assert a < 20


class TestATR:
    def test_positive_on_varying(self) -> None:
        candles = make_candles([100, 105, 95, 102, 98] * 5)
        assert atr_last(candles, 14) > 0

    def test_zero_insufficient(self) -> None:
        candles = make_candles([100, 101])
        assert atr_last(candles, 14) == 0.0


class TestEMA:
    def test_uptrend_ema_above_start(self) -> None:
        candles = make_candles([100 + i for i in range(30)])
        e = ema_last(candles, 10)
        assert e > 100


class TestExtractFeatures:
    def test_returns_four_dim(self) -> None:
        candles = make_candles([100 + i for i in range(30)])
        fv = extract_features(candles)
        assert fv.dim == 4
        assert len(fv.as_tuple()) == 4
