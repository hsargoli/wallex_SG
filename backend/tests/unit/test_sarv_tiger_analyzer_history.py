"""SarvTiger analyzer — historical window archive (TDD RED first)."""
import pytest
from decimal import Decimal
from app.domain.entities.candle import Candle
from app.services.bots.sarv_tiger.analyzer.history import (
    HistoricalWindow,
    build_windows,
    check_hit_sl_tp,
    compute_outcome,
    HORIZON_24H, HORIZON_72H, HORIZON_168H,
)


def _c(ts, o, h, l, c, v="100"):
    return Candle(
        time=ts, open=Decimal(str(o)), high=Decimal(str(h)),
        low=Decimal(str(l)), close=Decimal(str(c)),
        volume=Decimal(str(v)),
    )


def _linear(n, start=100.0, step=1.0, ts_start=1609459200, ts_step=14400):
    """Linear trending candles, seconds timestamps, ts_step=4h."""
    out = []
    for i in range(n):
        p = start + i * step
        out.append(_c(ts_start + i * ts_step, p - 0.5, p + 1, p - 1, p))
    return out


class TestHistoricalWindow:
    def test_fields(self):
        w = HistoricalWindow(
            window_start_ts=100, window_end_ts=200,
            features=[0.1] * 10,
            outcome_24h=0.05, outcome_72h=0.1, outcome_168h=0.2,
            hit_sl_24h=False, hit_tp_24h=True,
        )
        assert w.window_start_ts == 100
        assert w.window_end_ts == 200
        assert len(w.features) == 10
        assert w.outcome_24h == 0.05
        assert w.hit_tp_24h is True

    def test_round_trip(self):
        w = HistoricalWindow(
            window_start_ts=100, window_end_ts=200,
            features=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
            outcome_24h=0.05, outcome_72h=0.1, outcome_168h=0.2,
            hit_sl_24h=False, hit_tp_24h=True,
        )
        d = w.to_dict()
        w2 = HistoricalWindow.from_dict(d)
        assert w2.window_start_ts == w.window_start_ts
        assert w2.features == w.features
        assert w2.hit_tp_24h == w.hit_tp_24h


class TestOutcomeCalculation:
    def test_outcome_linear_up(self):
        # prices 100, 101, ..., 199. end=0, horizon=6 → close[6]=106 → +6%
        candles = _linear(100, start=100, step=1)
        outcome = compute_outcome(candles, end_idx=0, horizon=6)
        assert outcome == pytest.approx(0.06)

    def test_outcome_linear_down(self):
        # prices 200, 199, ..., 101. end=0, horizon=6 → close[6]=194 → -3%
        candles = _linear(100, start=200, step=-1)
        outcome = compute_outcome(candles, end_idx=0, horizon=6)
        assert outcome == pytest.approx(-0.03)

    def test_outcome_insufficient_future(self):
        candles = _linear(10, start=100, step=1)
        outcome = compute_outcome(candles, end_idx=8, horizon=6)
        assert outcome is None


class TestSLTP:
    def test_hit_sl(self):
        future = [_c(0, 99, 100, 94, 98)]  # low 94 <= sl 95
        sl_hit, tp_hit = check_hit_sl_tp(future, entry=100.0, sl=95.0, tp=120.0)
        assert sl_hit is True
        assert tp_hit is False

    def test_hit_tp(self):
        future = [_c(0, 101, 125, 100, 122)]  # high 125 >= tp 120
        sl_hit, tp_hit = check_hit_sl_tp(future, entry=100.0, sl=95.0, tp=120.0)
        assert sl_hit is False
        assert tp_hit is True

    def test_no_hit(self):
        future = [_c(0, 100, 105, 98, 103)]
        sl_hit, tp_hit = check_hit_sl_tp(future, entry=100.0, sl=95.0, tp=120.0)
        assert sl_hit is False
        assert tp_hit is False

    def test_sl_priority_within_same_candle(self):
        # low 90 <= sl 95 AND high 125 >= tp 120 → SL wins (conservative)
        future = [_c(0, 99, 125, 90, 95)]
        sl_hit, tp_hit = check_hit_sl_tp(future, entry=100.0, sl=95.0, tp=120.0)
        assert sl_hit is True
        assert tp_hit is False

    def test_tp_first_across_candles(self):
        # candle 0 hits TP first, candle 1 would hit SL but too late
        future = [
            _c(0, 101, 125, 100, 122),
            _c(1, 122, 122, 90, 95),
        ]
        sl_hit, tp_hit = check_hit_sl_tp(future, entry=100.0, sl=95.0, tp=120.0)
        assert sl_hit is False
        assert tp_hit is True


class TestBuildWindows:
    def test_count(self):
        # 100 candles: end_idx in [19, 57] → 39 windows
        candles = _linear(100)
        windows = build_windows(candles)
        assert len(windows) == 100 - 42 - 20 + 1

    def test_first_window_ts(self):
        candles = _linear(100)
        windows = build_windows(candles)
        w = windows[0]
        assert w.window_start_ts == int(candles[0].time)
        assert w.window_end_ts == int(candles[19].time)

    def test_insufficient_candles_returns_empty(self):
        candles = _linear(61)  # need >= 62
        windows = build_windows(candles)
        assert windows == []

    def test_deterministic(self):
        candles = _linear(100)
        w1 = build_windows(candles)
        w2 = build_windows(candles)
        assert [w.to_dict() for w in w1] == [w.to_dict() for w in w2]

    def test_no_lookahead_in_features(self):
        """Features at window i must NOT change if future candles change."""
        candles = _linear(100)
        windows_a = build_windows(candles)
        # Mutate last 10 candles (indices 90..99) — far future vs early windows
        for i in range(90, 100):
            c = candles[i]
            candles[i] = _c(
                int(c.time), float(c.open),
                float(c.open) * 2, float(c.open) * 0.5, float(c.open),
            )
        windows_b = build_windows(candles)
        # First window's features must be unchanged (no future leak)
        assert windows_a[0].features == windows_b[0].features
