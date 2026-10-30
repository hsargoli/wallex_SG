"""SarvTiger analyzer — timestamp normalization (TDD RED first)."""
import pytest
from app.services.bots.sarv_tiger.analyzer.timestamps import normalize_ts


class TestNormalizeTs:
    def test_10_digit_unchanged(self):
        assert normalize_ts(1609459200) == 1609459200

    def test_13_digit_converts_to_seconds(self):
        assert normalize_ts(1790805600000) == 1790805600

    def test_zero_edge_case(self):
        assert normalize_ts(0) == 0

    def test_negative_raises(self):
        with pytest.raises(ValueError):
            normalize_ts(-1)

    def test_boundary_10_digit_max(self):
        # 9999999999 = 2286-11-20 (still seconds, 10 digits)
        assert normalize_ts(9999999999) == 9999999999

    def test_boundary_13_digit_min(self):
        # 10000000000 = 2286-11-20 + 1s (ms, converts to 10000000)
        assert normalize_ts(10000000000) == 10000000
