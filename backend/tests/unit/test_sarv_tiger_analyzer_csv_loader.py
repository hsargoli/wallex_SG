"""SarvTiger analyzer — CSV loader with timestamp normalization (TDD RED first)."""
from decimal import Decimal
from pathlib import Path
from app.services.bots.sarv_tiger.analyzer.csv_loader import load_candles_csv


HEADER = "open_time,open,high,low,close,volume\n"


def _write(tmp_path: Path, rows: list[str]) -> Path:
    p = tmp_path / "test.csv"
    p.write_text(HEADER + "\n".join(rows) + "\n")
    return p


class TestLoadCandlesCsv:
    def test_basic_3_rows(self, tmp_path):
        p = _write(tmp_path, [
            "1609459200,100.0,101.0,99.0,100.5,1000.0",
            "1609462800,100.5,102.0,100.0,101.5,1100.0",
            "1609466400,101.5,103.0,101.0,102.5,1200.0",
        ])
        candles = load_candles_csv(p)
        assert len(candles) == 3
        assert int(candles[0].time) == 1609459200
        assert float(candles[0].open) == 100.0
        assert float(candles[2].close) == 102.5

    def test_normalizes_13_digit_ts(self, tmp_path):
        p = _write(tmp_path, [
            "1609459200,100.0,101.0,99.0,100.5,1000.0",
            "1790805600000,200.0,201.0,199.0,200.5,2000.0",
        ])
        candles = load_candles_csv(p)
        assert int(candles[0].time) == 1609459200
        assert int(candles[1].time) == 1790805600

    def test_mixed_ts_all_seconds(self, tmp_path):
        p = _write(tmp_path, [
            "1609459200,100.0,101.0,99.0,100.5,1000.0",
            "1790805600000,200.0,201.0,199.0,200.5,2000.0",
            "1609462800,100.5,102.0,100.0,101.5,1100.0",
        ])
        candles = load_candles_csv(p)
        for c in candles:
            assert int(c.time) < 10_000_000_000

    def test_header_only_returns_empty(self, tmp_path):
        p = tmp_path / "empty.csv"
        p.write_text(HEADER)
        assert load_candles_csv(p) == []

    def test_preserves_ohlcv_as_decimal(self, tmp_path):
        p = _write(tmp_path, ["1609459200,100.123,101.456,99.789,100.5,1000.5"])
        c = load_candles_csv(p)[0]
        assert c.open == Decimal("100.123")
        assert c.high == Decimal("101.456")
        assert c.low == Decimal("99.789")
        assert c.close == Decimal("100.5")
        assert c.volume == Decimal("1000.5")
