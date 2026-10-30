"""Historical window archive for pattern matching (sarv_tiger analyzer).

Each HistoricalWindow captures:
  - the N-candle pattern (features)
  - its exact time boundaries (window_start_ts, window_end_ts) — for
    leakage-safe filtering in similarity.py
  - forward outcomes (24h, 72h, 168h) and SL/TP hit flags (24h)

Design decisions:
  - window_end_ts is REQUIRED for leakage-safe similarity. A window
    whose 168h outcome is not yet known at time T cannot be used to
    predict at time T.
  - features stored as list[float] for JSON serialization. Convert to
    np.ndarray in similarity.py.
  - Windows with insufficient future are skipped (no partial outcomes).
  - Deterministic: no random, no now().
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.domain.entities.candle import Candle
from app.services.bots.sarv_tiger.analyzer.features import extract_features

# 4h timeframe horizons (in candle counts)
HORIZON_24H = 6    # 24 / 4
HORIZON_72H = 18   # 72 / 4
HORIZON_168H = 42  # 168 / 4

DEFAULT_WINDOW = 20
ATR_PERIOD = 14
SL_ATR_MULT = 1.2   # matches SarvTigerConfig.sl_atr_mult
TP_ATR_MULT = 8.0   # matches SarvTigerConfig.tp_atr_mult


@dataclass(slots=True)
class HistoricalWindow:
    window_start_ts: int
    window_end_ts: int
    features: list[float]
    outcome_24h: float
    outcome_72h: float
    outcome_168h: float
    hit_sl_24h: bool
    hit_tp_24h: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "window_start_ts": self.window_start_ts,
            "window_end_ts": self.window_end_ts,
            "features": list(self.features),
            "outcome_24h": self.outcome_24h,
            "outcome_72h": self.outcome_72h,
            "outcome_168h": self.outcome_168h,
            "hit_sl_24h": self.hit_sl_24h,
            "hit_tp_24h": self.hit_tp_24h,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "HistoricalWindow":
        return cls(
            window_start_ts=int(d["window_start_ts"]),
            window_end_ts=int(d["window_end_ts"]),
            features=[float(x) for x in d["features"]],
            outcome_24h=float(d["outcome_24h"]),
            outcome_72h=float(d["outcome_72h"]),
            outcome_168h=float(d["outcome_168h"]),
            hit_sl_24h=bool(d["hit_sl_24h"]),
            hit_tp_24h=bool(d["hit_tp_24h"]),
        )


def compute_outcome(
    candles: list[Candle], end_idx: int, horizon: int,
) -> float | None:
    """Percent change from close[end_idx] to close[end_idx+horizon].

    Returns None if:
      - end_idx < 0
      - end_idx + horizon >= len(candles) (insufficient future)
      - entry close is zero
    """
    if end_idx < 0:
        return None
    target = end_idx + horizon
    if target >= len(candles):
        return None
    entry = float(candles[end_idx].close)
    if entry == 0.0:
        return None
    return (float(candles[target].close) - entry) / entry


def check_hit_sl_tp(
    future: list[Candle], entry: float, sl: float, tp: float,
) -> tuple[bool, bool]:
    """Return (sl_hit, tp_hit) scanning future candles in order.

    Rules:
      - Within a candle: SL has priority (conservative). If both low<=sl
        and high>=tp in the same candle, count SL only.
      - Across candles: the first hit chronologically wins. Once TP is
        hit in an earlier candle, a later SL does not count (and vice
        versa).
    """
    for c in future:
        low = float(c.low)
        high = float(c.high)
        if low <= sl:
            return True, False
        if high >= tp:
            return False, True
    return False, False


def _atr_at(
    candles: list[Candle], end_idx: int, period: int = ATR_PERIOD,
) -> float:
    """Simple ATR (mean of true ranges) at end_idx. 0.0 if insufficient."""
    if end_idx < period:
        return 0.0
    trs: list[float] = []
    for i in range(end_idx - period + 1, end_idx + 1):
        h = float(candles[i].high)
        l = float(candles[i].low)
        prev_c = float(candles[i - 1].close)
        trs.append(max(h - l, abs(h - prev_c), abs(l - prev_c)))
    return sum(trs) / period


def build_windows(
    candles: list[Candle],
    window: int = DEFAULT_WINDOW,
    sl_atr_mult: float = SL_ATR_MULT,
    tp_atr_mult: float = TP_ATR_MULT,
    min_future: int = HORIZON_168H,
) -> list[HistoricalWindow]:
    """Build archive of historical windows with outcomes.

    For each valid end_idx in [window-1, len(candles)-min_future-1],
    extract the window's features, compute forward outcomes, and record
    whether SL/TP was hit within the 24h horizon.

    Returns [] if len(candles) < window + min_future (not enough data
    to form even one complete window with full outcomes).
    """
    n = len(candles)
    if n < window + min_future:
        return []

    result: list[HistoricalWindow] = []
    first_end = window - 1
    last_end = n - min_future - 1  # inclusive

    for end_idx in range(first_end, last_end + 1):
        start_idx = end_idx - window + 1
        window_candles = candles[start_idx : end_idx + 1]

        feats = extract_features(window_candles, window=window)
        if feats is None:
            continue

        entry = float(candles[end_idx].close)
        if entry <= 0.0:
            continue

        o24 = compute_outcome(candles, end_idx, HORIZON_24H)
        o72 = compute_outcome(candles, end_idx, HORIZON_72H)
        o168 = compute_outcome(candles, end_idx, HORIZON_168H)
        if o24 is None or o72 is None or o168 is None:
            continue

        atr_val = _atr_at(candles, end_idx, period=ATR_PERIOD)
        if atr_val <= 0.0:
            continue

        sl = entry - sl_atr_mult * atr_val
        tp = entry + tp_atr_mult * atr_val

        future_24h = candles[end_idx + 1 : end_idx + 1 + HORIZON_24H]
        sl_hit, tp_hit = check_hit_sl_tp(future_24h, entry=entry, sl=sl, tp=tp)

        result.append(HistoricalWindow(
            window_start_ts=int(candles[start_idx].time),
            window_end_ts=int(candles[end_idx].time),
            features=[float(x) for x in feats],
            outcome_24h=o24,
            outcome_72h=o72,
            outcome_168h=o168,
            hit_sl_24h=sl_hit,
            hit_tp_24h=tp_hit,
        ))

    return result
