"""Phase 2D-1: ADX indicator (Wilder's)."""
from decimal import Decimal
import pytest
from app.domain.entities.candle import Candle


def _c(t, h, l, c, o=None):
    o = o if o is not None else c
    return Candle(time=t, open=Decimal(str(o)), high=Decimal(str(h)),
                  low=Decimal(str(l)), close=Decimal(str(c)),
                  volume=Decimal("100"))


def _strong_uptrend(n=100):
    candles = []
    for i in range(n):
        base = 100 + i * 2
        candles.append(_c(i*3600, base + 1, base - 1, base + 0.5, base))
    return candles


def _flat_market(n=100):
    return [_c(i*3600, 101, 99, 100, 100) for i in range(n)]


class TestADX:
    def test_returns_list_same_length(self):
        from app.services.indicators import adx
        candles = _flat_market(100)
        vals = adx(candles, 14)
        assert len(vals) == 100

    def test_strong_uptrend_high_adx(self):
        from app.services.indicators import adx
        candles = _strong_uptrend(100)
        vals = adx(candles, 14)
        last = vals[-1]
        assert last is not None
        assert float(last) > 25, f"uptrend ADX should be >25, got {last}"

    def test_flat_market_low_adx(self):
        from app.services.indicators import adx
        candles = _flat_market(100)
        vals = adx(candles, 14)
        last = vals[-1]
        assert last is not None
        assert float(last) < 20, f"flat ADX should be <20, got {last}"

    def test_insufficient_data_returns_none(self):
        from app.services.indicators import adx
        candles = _flat_market(10)
        vals = adx(candles, 14)
        assert len(vals) == 10
        assert all(v is None for v in vals)
