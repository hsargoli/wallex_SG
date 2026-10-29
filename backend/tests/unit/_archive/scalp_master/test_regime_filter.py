"""Phase 2B-1: regime filter blocks entries in strong uptrends."""
from decimal import Decimal
from app.domain.entities.candle import Candle
from app.services.bots.scalp_master.config import ScalpMasterConfig
from app.services.bots.scalp_master.strategy import (
    is_uptrend_unfavorable, evaluate_entry,
)


def _c(t, close):
    v = Decimal(str(close))
    return Candle(time=t, open=v, high=v, low=v, close=v, volume=Decimal("100"))


class TestRegimeFilter:
    def test_disabled_returns_false(self):
        candles = [_c(i*3600, 100 + i) for i in range(100)]
        cfg = ScalpMasterConfig(trend_filter_enabled=False)
        assert is_uptrend_unfavorable(candles, cfg) is False

    def test_strong_uptrend_returns_true(self):
        candles = [_c(i*3600, 100 + i*2) for i in range(100)]
        cfg = ScalpMasterConfig(trend_filter_enabled=True, trend_ema_gap_pct=3.0)
        assert is_uptrend_unfavorable(candles, cfg) is True

    def test_downtrend_returns_false(self):
        candles = [_c(i*3600, 300 - i*2) for i in range(100)]
        cfg = ScalpMasterConfig(trend_filter_enabled=True, trend_ema_gap_pct=3.0)
        assert is_uptrend_unfavorable(candles, cfg) is False

    def test_flat_market_returns_false(self):
        candles = [_c(i*3600, 100) for i in range(100)]
        cfg = ScalpMasterConfig(trend_filter_enabled=True, trend_ema_gap_pct=3.0)
        assert is_uptrend_unfavorable(candles, cfg) is False

    def test_entry_blocked_in_uptrend(self):
        candles = [_c(i*3600, 100 + i*2) for i in range(100)]
        cfg = ScalpMasterConfig(trend_filter_enabled=True, trend_ema_gap_pct=3.0)
        assert evaluate_entry(candles, cfg) is None
