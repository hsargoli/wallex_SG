"""Feature extraction for historical pattern matching (sarv_tiger analyzer).

Converts a window of N 4h candles into a fixed-length feature vector,
normalized for cosine similarity. All features are in a comparable scale.

Design:
  - 10 features (returns, volatility, up/down, wick ratios, RSI, ATR, BB pos)
  - Normalization: z-score on train stats when provided (production use);
    raw clipped to [-3, 3] when not (early tests / one-off analysis)
  - No data leakage: mean/std must come from train split only
  - Deterministic: no random, no now()
"""
from __future__ import annotations

import numpy as np

from app.domain.entities.candle import Candle

N_FEATURES = 10
CLIP_MIN = -3.0
CLIP_MAX = 3.0
EPS = 1e-9


def _safe_div(num: float, den: float, default: float = 0.0) -> float:
    """Division with zero-guard."""
    return num / den if abs(den) > EPS else default


def _rsi_last(closes: np.ndarray, period: int = 14) -> float:
    """Last RSI value. Returns 50.0 (neutral) if insufficient or flat."""
    if len(closes) < period + 1:
        return 50.0
    deltas = np.diff(closes[-(period + 1):])
    gains = float(deltas[deltas > 0].sum())
    losses = float(-deltas[deltas < 0].sum())
    if losses < EPS:
        return 100.0 if gains > EPS else 50.0
    rs = gains / losses
    return 100.0 - 100.0 / (1.0 + rs)


def _atr_last(candles: list[Candle], period: int = 14) -> float:
    """Simple ATR (mean of true ranges). Returns 0.0 if insufficient."""
    if len(candles) < period + 1:
        return 0.0
    trs: list[float] = []
    for i in range(-period, 0):
        h = float(candles[i].high)
        l = float(candles[i].low)
        prev_c = float(candles[i - 1].close)
        tr = max(h - l, abs(h - prev_c), abs(l - prev_c))
        trs.append(tr)
    return sum(trs) / period


def extract_features(
    candles: list[Candle],
    window: int = 20,
    train_mean: np.ndarray | None = None,
    train_std: np.ndarray | None = None,
) -> np.ndarray | None:
    """Extract N_FEATURES normalized features from last `window` candles.

    Args:
        candles: full candle history (must have >= window candles).
        window: number of candles in the pattern.
        train_mean: per-feature mean from train split (for z-score).
        train_std: per-feature std from train split (for z-score).

    Returns:
        np.ndarray of shape (N_FEATURES,) clipped to [CLIP_MIN, CLIP_MAX],
        or None if insufficient candles.

    Note:
        For production use, train_mean/train_std are REQUIRED to prevent
        data leakage. When omitted, raw features are clipped to [-3, 3]
        — only safe for tests and one-off analysis.
    """
    if len(candles) < window:
        return None

    w = candles[-window:]
    opens = np.array([float(c.open) for c in w], dtype=float)
    highs = np.array([float(c.high) for c in w], dtype=float)
    lows = np.array([float(c.low) for c in w], dtype=float)
    closes = np.array([float(c.close) for c in w], dtype=float)
    volumes = np.array([float(c.volume) for c in w], dtype=float)

    # 1. Returns (window-level)
    ret = _safe_div(closes[-1] - closes[0], closes[0])

    # 2. Volatility (std of per-candle returns)
    pct_returns = np.diff(closes) / (closes[:-1] + EPS)
    vol = float(np.std(pct_returns)) if len(pct_returns) > 0 else 0.0

    # 3. Up/Down ratio in [-1, 1]
    n_up = int(np.sum(closes > opens))
    n_down = int(np.sum(closes < opens))
    up_down = _safe_div(float(n_up - n_down), float(n_up + n_down))

    # 4. Body ratio
    bodies = np.abs(closes - opens)
    ranges = np.maximum(highs - lows, EPS)
    body_ratio = float(np.mean(bodies / ranges))

    # 5. Upper wick ratio
    upper_wicks = np.maximum(highs - np.maximum(opens, closes), 0.0)
    upper_ratio = float(np.mean(upper_wicks / ranges))

    # 6. Lower wick ratio
    lower_wicks = np.maximum(np.minimum(opens, closes) - lows, 0.0)
    lower_ratio = float(np.mean(lower_wicks / ranges))

    # 7. Volume ratio (last vs avg of previous, centered at 0)
    if len(volumes) > 1:
        vol_avg = float(np.mean(volumes[:-1]))
        vol_ratio = _safe_div(volumes[-1], vol_avg) - 1.0
    else:
        vol_ratio = 0.0

    # 8. RSI normalized to [-1, 1]
    rsi = _rsi_last(closes, period=14)
    rsi_norm = (rsi - 50.0) / 50.0

    # 9. ATR as pct of close
    atr_val = _atr_last(candles, period=14)
    atr_pct = _safe_div(atr_val, float(closes[-1]))

    # 10. Position in BB (0=lower, 1=upper; 0.5 if flat)
    bb_window = closes[-min(20, len(closes)):]
    bb_mid = float(np.mean(bb_window))
    bb_std_val = float(np.std(bb_window))
    bb_upper = bb_mid + 2.0 * bb_std_val
    bb_lower = bb_mid - 2.0 * bb_std_val
    bb_pos = _safe_div(closes[-1] - bb_lower, bb_upper - bb_lower, default=0.5)

    raw = np.array([
        ret, vol, up_down, body_ratio, upper_ratio,
        lower_ratio, vol_ratio, rsi_norm, atr_pct, bb_pos,
    ], dtype=float)

    # Replace NaN/inf
    raw = np.where(np.isfinite(raw), raw, 0.0)

    # Normalize
    if train_mean is not None and train_std is not None:
        safe_std = np.where(np.abs(train_std) > EPS, train_std, 1.0)
        normalized = (raw - train_mean) / safe_std
    else:
        normalized = raw

    return np.clip(normalized, CLIP_MIN, CLIP_MAX)
