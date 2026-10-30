"""OHLCV resampling for sarv_tiger analyzer.

Combines N consecutive lower-timeframe candles into one higher-timeframe
candle:
  - open  = first.open
  - high  = max(all.high)
  - low   = min(all.low)
  - close = last.close
  - volume= sum(all.volume)
  - time  = first.time  (start of the group)

Partial groups (at the end) are dropped. Assumes input is sorted by time
and evenly spaced (e.g., all 1h candles with no gaps). Gap handling is
out of scope for v1 — a candle with a gap is treated as-is.
"""
from __future__ import annotations

from decimal import Decimal

from app.domain.entities.candle import Candle


def resample_ohlc(candles: list[Candle], factor: int) -> list[Candle]:
    """Combine every `factor` consecutive candles into one.

    Args:
        candles: input candles, assumed sorted by time and evenly spaced.
        factor: positive integer; 4 → 1h becomes 4h.

    Returns:
        List of resampled candles. Length = len(candles) // factor.
        Partial group at the end is dropped.

    Raises:
        ValueError: if factor <= 0.
    """
    if factor <= 0:
        raise ValueError(f"factor must be positive, got {factor}")
    if factor == 1:
        return list(candles)

    n_groups = len(candles) // factor
    out: list[Candle] = []

    for g in range(n_groups):
        start = g * factor
        group = candles[start : start + factor]

        ts = int(group[0].time)
        o = group[0].open
        h = max(c.high for c in group)
        l = min(c.low for c in group)
        c_close = group[-1].close
        v = sum((c.volume for c in group), start=Decimal("0"))

        out.append(Candle(
            time=ts, open=o, high=h, low=l, close=c_close, volume=v,
        ))

    return out
