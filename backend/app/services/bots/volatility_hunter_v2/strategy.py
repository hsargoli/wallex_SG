"""استراتژی Volatility Hunter v2 — نسخه بهبودیافته.

بهبودها نسبت به v1:
  1. Range detection با percentile (مقاوم به outlier)
  2. فیلتر ADX (تأیید رنج بودن)
  3. فیلتر حجم
  4. تأیید ورود با RSI
  5. SL/TP بر مبنای ATR (پویا)
  6. Range consistency check

منطق:
  1. بازار رنجه؟ (ADX < 25)
  2. دامنه‌ی range کافیه؟ (3%-15%)
  3. قیمت نزدیک کف range است؟ (پایین 15%)
  4. RSI اشباع فروش؟ (20-45)
  5. حجم معمولی؟
  → BUY

  خروج:
  - SL/TP بر مبنای ATR
  - Breakout از range
  - Timeout
"""

from dataclasses import dataclass

from app.domain.entities.candle import Candle
from app.services.bots.volatility_hunter_v2.config import VolatilityHunterV2Config
from app.services.indicators import atr, rsi, volume_sma


# ============================================================
# Data structures
# ============================================================


@dataclass(slots=True)
class RangeInfoV2:
    """اطلاعات range."""

    is_valid: bool
    low: float               # صدک پایین
    high: float              # صدک بالا
    mid: float
    range_pct: float
    atr: float
    atr_pct: float
    position_in_range: float  # 0 = کف، 1 = سقف
    volume_ratio: float       # حجم فعلی / میانگین
    adx: float
    rsi: float


@dataclass(slots=True)
class VolatilitySignalV2:
    """سیگنال ورود."""

    should_trade: bool
    action: str              # "buy" | "hold"
    entry_price: float
    stop_loss: float
    take_profit: float
    reason: str
    confidence: int          # 0-100
    range_info: RangeInfoV2 | None = None


# ============================================================
# Helpers
# ============================================================


def _last(values):
    for v in reversed(values):
        if v is not None:
            return v
    return None


def _percentile(sorted_values: list[float], pct: float) -> float:
    """محاسبه‌ی percentile (linear interpolation)."""
    if not sorted_values:
        return 0.0
    k = (len(sorted_values) - 1) * (pct / 100.0)
    f = int(k)
    c = min(f + 1, len(sorted_values) - 1)
    if f == c:
        return sorted_values[f]
    d = k - f
    return sorted_values[f] + (sorted_values[c] - sorted_values[f]) * d


def _calc_adx(candles: list[Candle], period: int = 14) -> float:
    """محاسبه ADX — اندازه‌ی قدرت روند (پایین = رنج)."""
    if len(candles) < period + 2:
        return 100.0  # فرض کن روند است (محتاطانه)

    trs, plus_dm, minus_dm = [], [], []
    for i in range(1, len(candles)):
        h = float(candles[i].high)
        l = float(candles[i].low)
        ph = float(candles[i - 1].high)
        pl = float(candles[i - 1].low)
        pc = float(candles[i - 1].close)

        tr = max(h - l, abs(h - pc), abs(l - pc))
        trs.append(tr)

        up = h - ph
        dn = pl - l
        plus_dm.append(up if up > dn and up > 0 else 0)
        minus_dm.append(dn if dn > up and dn > 0 else 0)

    if len(trs) < period:
        return 100.0

    atr_v = sum(trs[:period]) / period
    p_avg = sum(plus_dm[:period]) / period
    m_avg = sum(minus_dm[:period]) / period

    dx_vals = []
    for i in range(period, len(trs)):
        atr_v = (atr_v * (period - 1) + trs[i]) / period
        p_avg = (p_avg * (period - 1) + plus_dm[i]) / period
        m_avg = (m_avg * (period - 1) + minus_dm[i]) / period
        if atr_v == 0:
            continue
        pdi = 100 * p_avg / atr_v
        mdi = 100 * m_avg / atr_v
        s = pdi + mdi
        if s > 0:
            dx_vals.append(100 * abs(pdi - mdi) / s)

    if not dx_vals:
        return 100.0
    return sum(dx_vals[-period:]) / min(period, len(dx_vals))


# ============================================================
# Range detection (improved)
# ============================================================


def detect_range_v2(
    candles: list[Candle],
    config: VolatilityHunterV2Config,
) -> RangeInfoV2:
    """کشف range با percentile (مقاوم به outlier)."""
    if len(candles) < config.lookback_candles:
        return RangeInfoV2(False, 0, 0, 0, 0, 0, 0, 0.5, 0, 100, 50)

    recent = candles[-config.lookback_candles:]
    current = candles[-1]
    price = float(current.close)

    # ---------- ۱. Percentile-based range ----------
    highs = sorted(float(c.high) for c in recent)
    lows = sorted(float(c.low) for c in recent)

    high = _percentile(highs, config.range_high_pct)
    low = _percentile(lows, config.range_low_pct)

    if low <= 0:
        return RangeInfoV2(False, 0, 0, 0, 0, 0, 0, 0.5, 0, 100, 50)

    range_pct = (high - low) / low * 100
    mid = (high + low) / 2

    # ---------- ۲. ATR ----------
    atr_vals = atr(candles, 14)
    atr_v = _last(atr_vals)
    atr_f = float(atr_v) if atr_v else 0
    atr_pct = (atr_f / price * 100) if price > 0 else 0

    # ---------- ۳. موقعیت در range ----------
    if high > low:
        pos = (price - low) / (high - low)
        pos = max(0.0, min(1.0, pos))  # clamp
    else:
        pos = 0.5

    # ---------- ۴. حجم ----------
    # نکته: کندل آخر ممکنه ناقص باشه (کندل جاری).
    # از کندل قبلی (کامل) استفاده می‌کنیم.
    vol_ma = volume_sma(candles, 20)
    vma = _last(vol_ma)
    if vma and float(vma) > 0:
        # اگه طول کندل‌ها کافیه، از کندل قبلی استفاده کن (کامل شده)
        if len(candles) >= 2:
            last_closed_volume = float(candles[-2].volume)
        else:
            last_closed_volume = float(current.volume)
        volume_ratio = last_closed_volume / float(vma)
    else:
        volume_ratio = 1.0

    # ---------- ۵. ADX ----------
    adx_val = _calc_adx(candles, 14)

    # ---------- ۶. RSI ----------
    rsi_vals = rsi(candles, 14)
    rsi_v = _last(rsi_vals)
    rsi_val = float(rsi_v) if rsi_v else 50.0

    # ---------- ۷. اعتبار range ----------
    is_valid = (
        config.min_range_pct <= range_pct <= config.max_range_pct
        and atr_pct >= config.min_atr_pct
        and adx_val <= config.max_adx
        and volume_ratio >= config.min_volume_ratio
    )

    return RangeInfoV2(
        is_valid=is_valid,
        low=low,
        high=high,
        mid=mid,
        range_pct=range_pct,
        atr=atr_f,
        atr_pct=atr_pct,
        position_in_range=pos,
        volume_ratio=volume_ratio,
        adx=adx_val,
        rsi=rsi_val,
    )


# ============================================================
# Entry
# ============================================================


def evaluate_entry_v2(
    candles: list[Candle],
    config: VolatilityHunterV2Config,
) -> VolatilitySignalV2 | None:
    """تصمیم ورود v2."""
    if len(candles) < config.warmup_candles:
        return None

    current = candles[-1]
    price = float(current.close)

    rng = detect_range_v2(candles, config)
    if not rng.is_valid:
        return None

    # ---------- ۱. قیمت نزدیک کف؟ ----------
    buy_threshold = rng.low + (rng.high - rng.low) * (config.buy_zone_pct / 100)
    if price > buy_threshold:
        return None

    # ---------- ۲. RSI در محدوده؟ ----------
    if not (config.min_rsi <= rng.rsi <= config.max_rsi):
        return None

    # ---------- ۳. SL/TP بر مبنای ATR ----------
    if rng.atr <= 0:
        return None

    sl = price - (config.sl_atr_mult * rng.atr)
    tp = price + (config.tp_atr_mult * rng.atr)

    # اطمینان: SL نباید زیر range low باشه (اگه خیلی نزدیکه)
    # و TP نباید خیلی پایین‌تر از range high باشه
    sl = max(sl, rng.low * 0.995)  # کمی زیر range low
    tp = min(tp, rng.high * 1.005)  # کمی زیر range high

    # اطمینان: نسبت R/R حداقل 1.5
    risk = price - sl
    reward = tp - price
    if risk <= 0 or reward / risk < 1.5:
        return None

    # ---------- ۴. Confidence ----------
    confidence = 50
    if rng.position_in_range < 0.08:
        confidence += 15
    if rng.rsi < 35:
        confidence += 10
    if rng.adx < 20:
        confidence += 10
    if rng.volume_ratio > 1.0:
        confidence += 10
    confidence = min(95, confidence)

    return VolatilitySignalV2(
        should_trade=True,
        action="buy",
        entry_price=price,
        stop_loss=sl,
        take_profit=tp,
        reason=(
            f"کف range ({rng.position_in_range * 100:.1f}%) | "
            f"range={rng.range_pct:.1f}% | "
            f"ADX={rng.adx:.0f} | "
            f"RSI={rng.rsi:.0f} | "
            f"vol={rng.volume_ratio:.2f}x"
        ),
        confidence=confidence,
        range_info=rng,
    )


# ============================================================
# Exit
# ============================================================


def evaluate_exit_v2(
    candles: list[Candle],
    entry_price: float,
    stop_loss: float,
    take_profit: float,
    config: VolatilityHunterV2Config,
    candles_in_position: int = 0,
) -> tuple[bool, float, str]:
    """تصمیم خروج v2.

    Returns:
        (should_exit, exit_price, reason)
    """
    if not candles:
        return False, 0, ""

    current = candles[-1]
    high = float(current.high)
    low = float(current.low)
    price = float(current.close)

    # ---------- ۱. SL ----------
    if low <= stop_loss:
        return True, stop_loss, "stop_loss"

    # ---------- ۲. TP ----------
    if high >= take_profit:
        return True, take_profit, "take_profit"

    # ---------- ۳. Breakout ----------
    rng = detect_range_v2(candles, config)
    if rng.is_valid:
        if price > rng.high * (1 + config.breakout_pct / 100):
            return True, price, "breakout_up"
        if price < rng.low * (1 - config.breakout_pct / 100):
            return True, price, "breakout_down"

    # ---------- ۴. Timeout ----------
    if candles_in_position >= config.max_duration_candles:
        return True, price, "timeout"

    return False, 0, ""
