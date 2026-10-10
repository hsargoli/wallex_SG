"""Pure feature math — RSI, volatility, trend, volume_z.

هیچ import از numpy/sklearn/pandas. فقط math و statistics.
"""

from __future__ import annotations

import math
import statistics
from typing import Sequence

from app.domain.analysis.value_objects.feature_vector import FeatureVector
from app.domain.entities.candle import Candle

MIN_CANDLES = 15


def _closes(candles: Sequence[Candle]) -> list[float]:
    return [float(c.close) for c in candles]


def _volumes(candles: Sequence[Candle]) -> list[float]:
    return [float(c.volume) for c in candles]


def volatility(candles: Sequence[Candle]) -> float:
    """std pct_change × 100 (٪)."""
    closes = _closes(candles)
    if len(closes) < 2:
        return 0.0
    pct = [
        (closes[i] - closes[i - 1]) / closes[i - 1] * 100
        for i in range(1, len(closes))
        if closes[i - 1] != 0
    ]
    if len(pct) < 2:
        return 0.0
    return float(statistics.stdev(pct))


def rsi(candles: Sequence[Candle], period: int = 14) -> float:
    """RSI — میانگین سود/زیان."""
    closes = _closes(candles)
    if len(closes) < period + 1:
        return 50.0

    gains = 0.0
    losses = 0.0
    for i in range(1, period + 1):
        d = closes[i] - closes[i - 1]
        if d >= 0:
            gains += d
        else:
            losses -= d

    avg_gain = gains / period
    avg_loss = losses / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return float(100 - (100 / (1 + rs)))


def trend_strength(candles: Sequence[Candle]) -> float:
    """شیب رگرسیون خطی close، نرمالایز به ٪ از میانگین."""
    closes = _closes(candles)
    n = len(closes)
    if n < 2:
        return 0.0
    mean_x = (n - 1) / 2
    mean_y = sum(closes) / n
    num = sum((i - mean_x) * (closes[i] - mean_y) for i in range(n))
    den = sum((i - mean_x) ** 2 for i in range(n))
    if den == 0 or mean_y == 0:
        return 0.0
    slope = num / den
    return float(slope / mean_y * 100 * n)


def volume_z(candles: Sequence[Candle]) -> float:
    """z-score حجم آخرین کندل نسبت به پنجره."""
    vols = _volumes(candles)
    if len(vols) < 3:
        return 0.0
    try:
        m = statistics.mean(vols)
        s = statistics.stdev(vols)
    except statistics.StatisticsError:
        return 0.0
    if s == 0 or math.isnan(s):
        return 0.0
    return float((vols[-1] - m) / s)


def extract_features(candles: Sequence[Candle]) -> FeatureVector:
    """از یه پنجره، FeatureVector بساز."""
    return FeatureVector(
        volatility=volatility(candles),
        rsi=rsi(candles),
        trend_strength=trend_strength(candles),
        volume_z=volume_z(candles),
    )

# ============================================================
# atr_last, ema_last, adx — float-based (نه Decimal، برای ML)
# ============================================================


def _true_ranges(candles: Sequence[Candle]) -> list[float]:
    """TR[i] = max(high-low, |high-prev_close|, |low-prev_close|)."""
    out: list[float] = []
    for i in range(1, len(candles)):
        h = float(candles[i].high)
        l = float(candles[i].low)
        pc = float(candles[i - 1].close)
        out.append(max(h - l, abs(h - pc), abs(l - pc)))
    return out


def atr_last(candles: Sequence[Candle], period: int = 14) -> float:
    """ATR با Wilder's smoothing — آخرین مقدار (float)."""
    if period <= 0:
        raise ValueError("period must be positive")
    if len(candles) < period + 1:
        return 0.0
    trs = _true_ranges(candles)
    if len(trs) < period:
        return 0.0
    prev = sum(trs[:period]) / period
    for i in range(period, len(trs)):
        prev = (prev * (period - 1) + trs[i]) / period
    return float(prev)


def ema_last(candles: Sequence[Candle], period: int) -> float:
    """EMA — آخرین مقدار (float)."""
    if period <= 0:
        raise ValueError("period must be positive")
    if len(candles) < period:
        return 0.0
    closes = _closes(candles)
    mult = 2.0 / (period + 1)
    val = sum(closes[:period]) / period
    for i in range(period, len(closes)):
        val = (closes[i] - val) * mult + val
    return float(val)


def adx(candles: Sequence[Candle], period: int = 14) -> float:
    """ADX — قدرت روند (float). Wilder's smoothing."""
    if len(candles) < period + 1:
        return 0.0

    trs = _true_ranges(candles)
    plus_dm: list[float] = []
    minus_dm: list[float] = []
    for i in range(1, len(candles)):
        h = float(candles[i].high)
        l = float(candles[i].low)
        ph = float(candles[i - 1].high)
        pl = float(candles[i - 1].low)
        up = h - ph
        down = pl - l
        plus_dm.append(up if up > down and up > 0 else 0.0)
        minus_dm.append(down if down > up and down > 0 else 0.0)

    if len(trs) < period:
        return 0.0

    atr_v = sum(trs[:period]) / period
    plus_avg = sum(plus_dm[:period]) / period
    minus_avg = sum(minus_dm[:period]) / period
    dxs: list[float] = []
    for i in range(period, len(trs)):
        atr_v = (atr_v * (period - 1) + trs[i]) / period
        plus_avg = (plus_avg * (period - 1) + plus_dm[i]) / period
        minus_avg = (minus_avg * (period - 1) + minus_dm[i]) / period
        if atr_v == 0:
            continue
        plus_di = 100 * plus_avg / atr_v
        minus_di = 100 * minus_avg / atr_v
        s = plus_di + minus_di
        if s == 0:
            continue
        dxs.append(100 * abs(plus_di - minus_di) / s)

    if not dxs:
        return 0.0
    tail = dxs[-period:] if len(dxs) >= period else dxs
    return float(sum(tail) / len(tail))

