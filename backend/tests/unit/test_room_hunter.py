"""Unit tests for room_hunter: _count_clusters + detect_room.

Design (Di Parto):
- _count_clusters: pure function, edge cases (empty, single, contiguous, gaps, mixed)
- detect_room: validation (window/touches/tolerance), insufficient candles,
  floor <= 0, room detected, single-cluster warning (trend vs room)
"""
from decimal import Decimal

import pytest

from scripts.room_hunter import _count_clusters, detect_room
from app.domain.entities.candle import Candle


# ═══════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════

def _candle(t: int, high: str, low: str) -> Candle:
    """Build a minimal Candle with given high/low (open/close/volume dummy)."""
    return Candle(
        time=t,
        open=Decimal("100"),
        high=Decimal(high),
        low=Decimal(low),
        close=Decimal("100"),
        volume=Decimal("1"),
    )


# ═══════════════════════════════════════════════════════════════
# _count_clusters
# ═══════════════════════════════════════════════════════════════

class TestCountClusters:
    def test_empty_list_returns_zero(self):
        assert _count_clusters([]) == 0

    def test_single_index_returns_one(self):
        assert _count_clusters([5]) == 1

    def test_contiguous_returns_one(self):
        assert _count_clusters([0, 1, 2, 3]) == 1

    def test_all_gaps_returns_count(self):
        assert _count_clusters([0, 2, 4, 6]) == 4

    def test_mixed_clusters(self):
        # [0,1] + [3,4,5] + [7] = 3 clusters
        assert _count_clusters([0, 1, 3, 4, 5, 7]) == 3

    def test_two_clusters(self):
        assert _count_clusters([0, 1, 5, 6]) == 2

    def test_large_contiguous(self):
        assert _count_clusters(list(range(100))) == 1

    def test_large_gaps(self):
        assert _count_clusters(list(range(0, 100, 2))) == 50


# ═══════════════════════════════════════════════════════════════
# detect_room — validation
# ═══════════════════════════════════════════════════════════════

class TestDetectRoomValidation:
    def test_window_too_small_raises(self):
        candles = [_candle(i, "110", "90") for i in range(10)]
        with pytest.raises(SystemExit, match="invalid --window"):
            detect_room(candles, window=1, tol_pct=Decimal("0.5"), min_touches=2)

    def test_min_touches_too_small_raises(self):
        candles = [_candle(i, "110", "90") for i in range(10)]
        with pytest.raises(SystemExit, match="invalid --window"):
            detect_room(candles, window=5, tol_pct=Decimal("0.5"), min_touches=0)

    def test_negative_tolerance_raises(self):
        candles = [_candle(i, "110", "90") for i in range(10)]
        with pytest.raises(SystemExit, match="invalid --window"):
            detect_room(candles, window=5, tol_pct=Decimal("-1"), min_touches=2)

    def test_insufficient_candles_raises(self):
        candles = [_candle(i, "110", "90") for i in range(3)]
        with pytest.raises(SystemExit, match="need >= 10"):
            detect_room(candles, window=10, tol_pct=Decimal("0.5"), min_touches=2)

    def test_floor_zero_raises(self):
        candles = [_candle(i, "110", "0") for i in range(10)]
        with pytest.raises(SystemExit, match="floor <= 0"):
            detect_room(candles, window=10, tol_pct=Decimal("0.5"), min_touches=2)


# ═══════════════════════════════════════════════════════════════
# detect_room — detection logic
# ═══════════════════════════════════════════════════════════════

class TestDetectRoomDetection:
    def test_perfect_room_detected(self):
        # 10 candles: ceiling=110 (touches 4), floor=90 (touches 4)
        candles = []
        for i in range(10):
            if i % 2 == 0:
                candles.append(_candle(i, "110", "90"))
            else:
                candles.append(_candle(i, "100", "95"))
        r = detect_room(candles, window=10, tol_pct=Decimal("1"), min_touches=2)
        assert r["room_detected"] is True
        assert r["ceiling_touches"] == 5
        assert r["floor_touches"] == 5
        assert r["ceiling"] == "110"
        assert r["floor"] == "90"

    def test_not_enough_touches_no_room(self):
        # فقط ۱ کندل به سقف و ۱ کندل به کف
        candles = [_candle(i, "100", "95") for i in range(10)]
        candles[0] = _candle(0, "110", "95")
        candles[1] = _candle(1, "100", "90")
        r = detect_room(candles, window=10, tol_pct=Decimal("1"), min_touches=2)
        assert r["room_detected"] is False
        assert r["ceiling_touches"] == 1
        assert r["floor_touches"] == 1

    def test_single_cluster_warning_ceiling(self):
        # ۵ کندل پیوسته به سقف (high=110)، بقیه high=100
        # floor: فقط ۱ کندل low=95، بقیه low=100 (که <= 95.95 نیست)
        candles = [_candle(i, "100", "100") for i in range(10)]
        for i in range(0, 5):
            candles[i] = _candle(i, "110", "100")
        candles[0] = _candle(0, "110", "95")  # فقط ۱ floor touch
        r = detect_room(candles, window=10, tol_pct=Decimal("1"), min_touches=2)
        assert r["ceiling_single_cluster"] is True
        assert r["ceiling_clusters"] == 1
        assert r["floor_touches"] == 1
        assert r["floor_single_cluster"] is False
        assert r["room_detected"] is False  # floor touches < 2

    def test_two_clusters_no_warning(self):
        # ۲ کندل سقف جدا از هم → ۲ کلاستر → no warning
        candles = [_candle(i, "100", "95") for i in range(10)]
        candles[0] = _candle(0, "110", "95")
        candles[5] = _candle(5, "110", "95")
        candles[2] = _candle(2, "100", "90")
        candles[7] = _candle(7, "100", "90")
        r = detect_room(candles, window=10, tol_pct=Decimal("1"), min_touches=2)
        assert r["ceiling_clusters"] == 2
        assert r["ceiling_single_cluster"] is False
        assert r["floor_clusters"] == 2
        assert r["floor_single_cluster"] is False
        assert r["room_detected"] is True

    def test_output_keys_present(self):
        candles = [_candle(i, "110", "90") for i in range(10)]
        r = detect_room(candles, window=10, tol_pct=Decimal("0.5"), min_touches=2)
        expected_keys = {
            "window", "tolerance_pct", "min_touches", "candles_total",
            "window_start_time", "window_end_time",
            "ceiling", "floor", "range_pct",
            "ceiling_threshold", "floor_threshold",
            "ceiling_touches", "floor_touches",
            "ceiling_clusters", "floor_clusters",
            "ceiling_single_cluster", "floor_single_cluster",
            "ceiling_touch_times", "floor_touch_times",
            "room_detected",
        }
        assert set(r.keys()) == expected_keys

    def test_window_uses_last_n_candles(self):
        # 20 کندل: ۱۰ اول قیمت بالا، ۱۰ آخر اتاق
        candles = [_candle(i, "200", "150") for i in range(10)]
        for i in range(10, 20):
            if i % 2 == 0:
                candles.append(_candle(i, "110", "90"))
            else:
                candles.append(_candle(i, "100", "95"))
        r = detect_room(candles, window=10, tol_pct=Decimal("1"), min_touches=2)
        assert r["candles_total"] == 20
        assert r["ceiling"] == "110"
        assert r["floor"] == "90"
        assert r["room_detected"] is True

    def test_touch_times_correct(self):
        # کندل‌های ۰ و ۲ به سقف، ۱ و ۳ به کف
        candles = [
            _candle(0, "110", "95"),
            _candle(1, "100", "90"),
            _candle(2, "110", "95"),
            _candle(3, "100", "90"),
            _candle(4, "100", "95"),
        ]
        r = detect_room(candles, window=5, tol_pct=Decimal("1"), min_touches=2)
        assert r["ceiling_touch_times"] == [0, 2]
        assert r["floor_touch_times"] == [1, 3]
