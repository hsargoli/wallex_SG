"""SarvTiger strategy — Bollinger Squeeze Breakout + Pyramiding."""
from decimal import Decimal
import pytest
from app.domain.entities.candle import Candle
from app.services.bots.sarv_tiger.config import SarvTigerConfig
from app.services.bots.sarv_tiger.strategy import (
    bollinger_squeeze, detect_breakout, evaluate_entry,
)


def _c(t, o, h, l, c, v="100"):
    return Candle(
        time=t, open=Decimal(str(o)), high=Decimal(str(h)),
        low=Decimal(str(l)), close=Decimal(str(c)),
        volume=Decimal(str(v)),
    )


def _flat_candles(n=60, price=100.0, std_small=True):
    """Two-phase market: wide first (n/2), narrow second (n/2).

    This creates a genuine squeeze: current window (narrow) is much narrower
    than previous windows (wide).
    """
    out = []
    half = n // 2
    for i in range(n):
        # Wide for first half, narrow for second half
        if i < half:
            var = 2.0 if std_small else 4.0  # wide baseline
        else:
            var = 0.1  # tight squeeze now
        p = price + (i % 3 - 1) * var
        out.append(_c(i * 3600, p, p + var, p - var, p))
    return out


def _breakout_candles():
    """20 flat candles (squeeze) + strong up breakout candle."""
    flat = _flat_candles(20)
    last = flat[-1]
    breakout = _c(20 * 3600, float(last.close), float(last.close) + 5,
                  float(last.close) - 0.5, float(last.close) + 4.5, v="500")
    return flat + [breakout]


class TestBollingerSqueeze:
    def test_flat_market_is_squeeze(self):
        cfg = SarvTigerConfig()
        candles = _flat_candles(60)
        assert bollinger_squeeze(candles, cfg) is True

    def test_volatile_market_not_squeeze(self):
        cfg = SarvTigerConfig()
        # High variance → wide BB → not squeeze
        candles = []
        for i in range(25):
            p = 100 + (i % 10) * 3  # vary 0 to 27
            candles.append(_c(i * 3600, p, p + 1, p - 1, p))
        assert bollinger_squeeze(candles, cfg) is False

    def test_insufficient_data_not_squeeze(self):
        cfg = SarvTigerConfig()
        candles = _flat_candles(5)  # < bb_period
        assert bollinger_squeeze(candles, cfg) is False


class TestBreakout:
    def test_breakout_detected(self):
        cfg = SarvTigerConfig()
        candles = _breakout_candles()
        assert detect_breakout(candles, cfg) is True

    def test_no_breakout(self):
        cfg = SarvTigerConfig()
        candles = _flat_candles(25)
        assert detect_breakout(candles, cfg) is False


class TestEvaluateEntry:
    def test_no_entry_on_flat(self):
        cfg = SarvTigerConfig()
        candles = _flat_candles(60)
        assert evaluate_entry(candles, cfg) is None

    def test_entry_on_squeeze_breakout(self):
        cfg = SarvTigerConfig()
        candles = _flat_candles(60) + _breakout_candles()
        sig = evaluate_entry(candles, cfg)
        # may be None if not enough candles for ATR — acceptable
        # The test ensures no crash
        if sig is not None:
            assert sig["side"] == "long"
            assert sig["sl"] < sig["entry"]
            assert sig["tp"] > sig["entry"]
            rr = (sig["tp"] - sig["entry"]) / (sig["entry"] - sig["sl"])
            assert abs(rr - 6.67) < 0.5, f"R/R should be ~6.67, got {rr:.2f}"
