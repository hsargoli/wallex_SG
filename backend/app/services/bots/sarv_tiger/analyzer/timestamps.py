"""Timestamp normalization — single source of truth.

Mixed-format CSV issue: BTCUSDT_1h.csv has 10-digit (seconds) rows
before 2025-01-01 and 13-digit (milliseconds) after. All downstream
code assumes seconds. This module is the ONLY place that knows about
the two formats.

Rule: any int > 10_000_000_000 is milliseconds (year 2286+ in seconds).
Everything else is seconds.
"""
from __future__ import annotations

SECONDS_CUTOFF = 10_000_000_000  # 2286-11-20 in seconds


def normalize_ts(ts: int) -> int:
    """Return timestamp in seconds. Handles 10-digit and 13-digit input.

    Raises:
        ValueError: if ts is negative (invalid timestamp).
    """
    if ts < 0:
        raise ValueError(f"timestamp must be >= 0, got {ts}")
    if ts >= SECONDS_CUTOFF:
        return ts // 1000
    return ts
