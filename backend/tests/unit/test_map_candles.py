"""Unit tests for map_candles."""

from decimal import Decimal

import pytest

from app.infrastructure.exchange.wallex.mapper import map_candles


class TestMapCandles:
    def test_valid_response(self):
        raw = {
            "s": "ok",
            "t": [1000, 1060, 1120],
            "o": ["100", "101", "102"],
            "h": ["110", "111", "112"],
            "l": ["90", "91", "92"],
            "c": ["105", "106", "107"],
            "v": ["1.5", "2.5", "3.5"],
        }
        candles = map_candles(raw)
        assert len(candles) == 3
        c = candles[0]
        assert c.time == 1000
        assert c.open == Decimal("100")
        assert c.high == Decimal("110")
        assert c.low == Decimal("90")
        assert c.close == Decimal("105")
        assert c.volume == Decimal("1.5")

    def test_status_not_ok_returns_empty(self):
        raw = {"s": "no_data", "t": [], "o": [], "h": [], "l": [], "c": [], "v": []}
        assert map_candles(raw) == []

    def test_missing_status_returns_empty(self):
        assert map_candles({}) == []

    def test_mismatched_lengths_raises(self):
        raw = {
            "s": "ok",
            "t": [1000, 1060],
            "o": ["100"],
            "h": ["110", "111"],
            "l": ["90", "91"],
            "c": ["105", "106"],
            "v": ["1", "2"],
        }
        with pytest.raises(ValueError, match="mismatched"):
            map_candles(raw)

    def test_skips_invalid_numeric_rows(self):
        raw = {
            "s": "ok",
            "t": [1000, 1060, 1120],
            "o": ["100", "bad", "102"],
            "h": ["110", "111", "112"],
            "l": ["90", "91", "92"],
            "c": ["105", "106", "107"],
            "v": ["1", "2", "3"],
        }
        candles = map_candles(raw)
        # ردیف دوم به‌خاطر "bad" skip میشه
        assert len(candles) == 2
        assert candles[0].time == 1000
        assert candles[1].time == 1120

    def test_empty_arrays(self):
        raw = {"s": "ok", "t": [], "o": [], "h": [], "l": [], "c": [], "v": []}
        assert map_candles(raw) == []

    def test_decimal_precision_preserved(self):
        raw = {
            "s": "ok",
            "t": [1000],
            "o": ["12345.67890123456789"],
            "h": ["12345.67890123456790"],
            "l": ["12345.67890123456788"],
            "c": ["12345.67890123456789"],
            "v": ["0.00000001"],
        }
        candles = map_candles(raw)
        assert candles[0].open == Decimal("12345.67890123456789")
        assert candles[0].volume == Decimal("0.00000001")
