"""SarvTiger strategy — Bollinger Squeeze Breakout + Pyramiding."""
from __future__ import annotations

from decimal import Decimal

from app.domain.entities.candle import Candle
from app.services.indicators import atr
from app.services.bots.sarv_tiger.config import SarvTigerConfig


def _bollinger(
    candles: list[Candle], period: int, std_mult: float,
) -> tuple[float, float, float] | None:
    """Return (upper, middle, lower) of last candle, or None if insufficient."""
    if len(candles) < period:
        return None
    window = [float(c.close) for c in candles[-period:]]
    mean = sum(window) / period
    var = sum((x - mean) ** 2 for x in window) / period
    std = var ** 0.5
    upper = mean + std_mult * std
    lower = mean - std_mult * std
    return upper, mean, lower


def _bb_width(
    candles: list[Candle], period: int, std_mult: float,
) -> float | None:
    bb = _bollinger(candles, period, std_mult)
    if bb is None:
        return None
    upper, mid, lower = bb
    if mid <= 0:
        return None
    return (upper - lower) / mid


def bollinger_squeeze(candles: list[Candle], config: SarvTigerConfig) -> bool:
    """True if BB width now < squeeze_threshold × avg BB width (last N)."""
    if len(candles) < config.bb_period + config.bb_squeeze_window:
        return False

    current_width = _bb_width(candles, config.bb_period, config.bb_std)
    if current_width is None:
        return False

    widths: list[float] = []
    for i in range(1, config.bb_squeeze_window + 1):
        w = _bb_width(candles[:-i], config.bb_period, config.bb_std)
        if w is not None:
            widths.append(w)

    if not widths:
        return False
    avg_width = sum(widths) / len(widths)
    if avg_width <= 0:
        return False
    return current_width < (avg_width * config.bb_squeeze_threshold)


def detect_breakout(candles: list[Candle], config: SarvTigerConfig) -> bool:
    """True if last close > upper BB (upside breakout)."""
    bb = _bollinger(candles, config.bb_period, config.bb_std)
    if bb is None:
        return False
    upper, _, _ = bb
    last_close = float(candles[-1].close)
    return last_close > upper


def _last_atr(candles: list[Candle], period: int) -> float | None:
    if len(candles) < period + 1:
        return None
    vals = atr(candles, period)
    for v in reversed(vals):
        if v is not None:
            return float(v)
    return None


def evaluate_entry(
    candles: list[Candle], config: SarvTigerConfig,
) -> dict | None:
    """Long entry on squeeze + breakout.

    Returns dict with side, entry, sl, tp, reason, or None.
    """
    if len(candles) < config.bb_period + config.atr_period + 5:
        return None

    if not bollinger_squeeze(candles, config):
        return None
    if not detect_breakout(candles, config):
        return None

    atr_val = _last_atr(candles, config.atr_period)
    if atr_val is None or atr_val <= 0:
        return None

    entry = float(candles[-1].close)
    sl = entry - config.sl_atr_mult * atr_val
    tp = entry + config.tp_atr_mult * atr_val

    if sl >= entry or tp <= entry:
        return None  # sanity

    return {
        "side": "long",
        "entry": entry,
        "sl": sl,
        "tp": tp,
        "atr": atr_val,
        "reason": "bollinger_squeeze_breakout",
    }


def evaluate_exit(
    candles: list[Candle],
    entry: float,
    sl: float,
    tp: float,
    config: SarvTigerConfig,
) -> tuple[bool, float, str]:
    """Long exit check: SL, TP, or trailing."""
    if not candles:
        return False, 0.0, ""

    current = candles[-1]
    high = float(current.high)
    low = float(current.low)
    close = float(current.close)

    # SL first (conservative)
    if low <= sl:
        return True, sl, "stop_loss"
    # TP
    if high >= tp:
        return True, tp, "take_profit"

    return False, 0.0, ""
