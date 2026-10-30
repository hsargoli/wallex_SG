"""SarvTiger analyzer-only backtest — core logic (TDD RED first).

Only the deterministic core is unit-tested here:
    - split_train_test (time-based, not random — leakage-safe)
    - simulate_trade (SL/TP/time-exit decision on a single trade)
The heavy lifting (feature extraction, similarity, outcome analysis) is
already tested in its own modules. The script (`backtest_analyzer_only.py`)
wires them together and is validated by the smoke/full run output.
"""
import pytest
from decimal import Decimal
from app.domain.entities.candle import Candle
from app.services.bots.sarv_tiger.analyzer.backtest_analyzer_only import (
    split_train_test,
    simulate_trade,
)


def _c(ts, o, h, l, c):
    return Candle(
        time=ts,
        open=Decimal(str(o)), high=Decimal(str(h)),
        low=Decimal(str(l)),   close=Decimal(str(c)),
        volume=Decimal("100"),
    )


class TestSplitTrainTest:
    def test_70_30_default(self):
        items = list(range(100))
        train, test = split_train_test(items)
        assert len(train) == 70
        assert len(test) == 30
        assert train == items[:70]
        assert test == items[70:]

    def test_custom_ratio(self):
        items = list(range(100))
        train, test = split_train_test(items, train_ratio=0.5)
        assert len(train) == 50
        assert len(test) == 50

    def test_empty(self):
        train, test = split_train_test([])
        assert train == [] and test == []

    def test_preserves_order(self):
        items = ["a", "b", "c", "d", "e"]
        train, test = split_train_test(items, train_ratio=0.6)
        assert train == ["a", "b", "c"]
        assert test == ["d", "e"]

    def test_invalid_ratio_raises(self):
        with pytest.raises(ValueError):
            split_train_test([1, 2, 3], train_ratio=0.0)
        with pytest.raises(ValueError):
            split_train_test([1, 2, 3], train_ratio=1.0)
        with pytest.raises(ValueError):
            split_train_test([1, 2, 3], train_ratio=1.5)


class TestSimulateTrade:
    def test_tp_hit_first_candle(self):
        """Candle 0: high >= tp → exit at tp. Win."""
        future = [_c(0, 100, 125, 100, 122)]
        pnl, reason = simulate_trade(
            entry=100.0, sl=95.0, tp=120.0, future=future,
        )
        assert reason == "tp"
        assert pnl == pytest.approx((120.0 - 100.0) / 100.0)

    def test_sl_hit_first_candle(self):
        """Candle 0: low <= sl → exit at sl. Loss."""
        future = [_c(0, 100, 100, 90, 92)]
        pnl, reason = simulate_trade(
            entry=100.0, sl=95.0, tp=120.0, future=future,
        )
        assert reason == "sl"
        assert pnl == pytest.approx((95.0 - 100.0) / 100.0)

    def test_sl_priority_in_same_candle(self):
        """Both SL and TP within one candle → conservative: SL wins."""
        future = [_c(0, 100, 125, 90, 100)]
        pnl, reason = simulate_trade(
            entry=100.0, sl=95.0, tp=120.0, future=future,
        )
        assert reason == "sl"

    def test_time_exit(self):
        """No SL/TP → exit at last close in `future`."""
        future = [
            _c(0, 100, 105, 98, 103),
            _c(1, 103, 108, 102, 106),
        ]
        pnl, reason = simulate_trade(
            entry=100.0, sl=95.0, tp=120.0, future=future,
        )
        assert reason == "time"
        assert pnl == pytest.approx((106.0 - 100.0) / 100.0)

    def test_empty_future_returns_none(self):
        pnl, reason = simulate_trade(
            entry=100.0, sl=95.0, tp=120.0, future=[],
        )
        assert pnl is None
        assert reason == "no_future"

    def test_tp_first_then_sl_ignored(self):
        """TP in candle 0, SL would hit in candle 1 — TP wins (chronological)."""
        future = [
            _c(0, 101, 125, 100, 122),
            _c(1, 122, 122, 90, 95),
        ]
        pnl, reason = simulate_trade(
            entry=100.0, sl=95.0, tp=120.0, future=future,
        )
        assert reason == "tp"
