"""SarvTiger analyzer — 1h→4h OHLCV resampling (TDD RED first)."""
import pytest
from decimal import Decimal
from app.domain.entities.candle import Candle
from app.services.bots.sarv_tiger.analyzer.resample import resample_ohlc


def _c(ts, o, h, l, c, v="100"):
    return Candle(
        time=ts, open=Decimal(str(o)), high=Decimal(str(h)),
        low=Decimal(str(l)), close=Decimal(str(c)),
        volume=Decimal(str(v)),
    )


def _hourly(n, start_ts=1609459200):
    """n hourly candles with predictable OHLCV."""
    out = []
    for i in range(n):
        base = 100.0 + i
        out.append(_c(
            start_ts + i * 3600,
            base,
            base + 2.0,
            base - 1.0,
            base + 0.5,
            str(10 * (i + 1)),
        ))
    return out


class TestResampleOhlc:
    def test_basic_ohlc(self):
        out = resample_ohlc(_hourly(8), factor=4)
        assert len(out) == 2
        g0 = out[0]
        assert float(g0.open) == 100.0
        assert float(g0.high) == 105.0
        assert float(g0.low) == 99.0
        assert float(g0.close) == 103.5

    def test_volume_sum(self):
        out = resample_ohlc(_hourly(8), factor=4)
        assert float(out[0].volume) == 100.0   # 10+20+30+40
        assert float(out[1].volume) == 260.0   # 50+60+70+80

    def test_timestamp_first_of_group(self):
        out = resample_ohlc(_hourly(8, start_ts=1000000), factor=4)
        assert int(out[0].time) == 1000000
        assert int(out[1].time) == 1000000 + 4 * 3600

    def test_insufficient_returns_empty(self):
        assert resample_ohlc(_hourly(3), factor=4) == []

    def test_partial_group_dropped(self):
        out = resample_ohlc(_hourly(10), factor=4)
        assert len(out) == 2

    def test_empty_returns_empty(self):
        assert resample_ohlc([], factor=4) == []

    def test_factor_1_identity(self):
        candles = _hourly(4)
        out = resample_ohlc(candles, factor=1)
        assert len(out) == 4
        assert [int(c.time) for c in out] == [int(c.time) for c in candles]

    def test_factor_must_be_positive(self):
        with pytest.raises(ValueError):
            resample_ohlc(_hourly(8), factor=0)
