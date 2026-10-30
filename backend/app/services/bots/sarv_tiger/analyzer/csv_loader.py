"""CSV loader for sarv_tiger analyzer — timestamp normalization at the edge.

The BTCUSDT_1h.csv file is mixed: rows before 2025-01-01 use 10-digit
seconds, rows after use 13-digit milliseconds. This loader normalizes
EVERY timestamp to seconds via normalize_ts (single source of truth in
timestamps.py), so downstream code never has to care.

Columns expected: open_time,open,high,low,close,volume
"""
from __future__ import annotations

import csv
from decimal import Decimal
from pathlib import Path

from app.domain.entities.candle import Candle
from app.services.bots.sarv_tiger.analyzer.timestamps import normalize_ts


REQUIRED_COLUMNS = {"open_time", "open", "high", "low", "close", "volume"}


def load_candles_csv(path: Path | str) -> list[Candle]:
    """Load OHLCV candles from CSV, normalizing all timestamps to seconds.

    Args:
        path: CSV file path.

    Returns:
        List of Candle entities in file order (assumed chronological).

    Raises:
        FileNotFoundError: if path does not exist.
        ValueError: if required columns are missing.
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"CSV not found: {p}")

    candles: list[Candle] = []

    with p.open("r", newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            return []
        missing = REQUIRED_COLUMNS - set(reader.fieldnames)
        if missing:
            raise ValueError(
                f"CSV missing required columns: {sorted(missing)}"
            )

        for row in reader:
            raw_ts = int(row["open_time"])
            ts = normalize_ts(raw_ts)
            candles.append(Candle(
                time=ts,
                open=Decimal(row["open"]),
                high=Decimal(row["high"]),
                low=Decimal(row["low"]),
                close=Decimal(row["close"]),
                volume=Decimal(row["volume"]),
            ))

    return candles
