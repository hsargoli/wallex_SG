"""Bottom Detector — تشخیص کف‌های قیمت.

۵ نشانه‌ی کف:
  1. RSI Oversold (< 30)
  2. RSI Divergence (قیمت پایین‌تر، RSI بالاتر)
  3. Volume Spike (حجم ۲.۵× میانگین)
  4. Rejection Wick (سایه‌ی پایینی بلند)
  5. Support Touch (لمس حمایت)
"""

from dataclasses import dataclass, field
from decimal import Decimal

from app.domain.entities.candle import Candle
from app.services.indicators import rsi, volume_sma
from app.services.levels import find_swing_levels


@dataclass(slots=True)
class BottomSignal:
    """نتیجه‌ی تشخیص کف."""

    is_bottom: bool
    score: int  # 0-10
    strength: str  # none / weak / medium / strong
    reasons: list[str] = field(default_factory=list)
    price: Decimal = Decimal(0)
    time: int = 0


def _last(values):
    for v in reversed(values):
        if v is not None:
            return v
    return None


def _has_recent_bottom(candles: list[Candle], idx: int, hours: int = 4) -> bool:
    """آیا در N ساعت اخیر کف تشخیص داده شده؟ (جلوگیری از تکرار)"""
    if idx < 2:
        return False
    current_time = candles[idx].time
    threshold_sec = hours * 3600
    for j in range(max(0, idx - 10), idx):
        # چک سریع: فقط کندل‌های نزدیک
        if current_time - candles[j].time > threshold_sec:
            continue
        if current_time - candles[j].time < 0:
            continue
        prev_sig = detect_bottom(candles, idx=j, _internal=True)
        if prev_sig.is_bottom:
            return True
    return False


def detect_bottom(
    candles: list[Candle], idx: int | None = None, _internal: bool = False
) -> BottomSignal:
    """
    تشخیص کف در کندل شماره idx (پیش‌فرض: آخرین کندل).
    از کندل‌های [0..idx] استفاده می‌کنه (بدون نگاه به آینده).
    """
    if idx is None:
        idx = len(candles) - 1

    if idx < 30:
        return BottomSignal(is_bottom=False, score=0, strength="none")

    window = candles[: idx + 1]
    current = candles[idx]

    reasons: list[str] = []
    score = 0

    # ---------- ۱. RSI Oversold ----------
    rsi_values = rsi(window, 14)
    current_rsi = _last(rsi_values)

    if current_rsi is not None:
        if current_rsi < Decimal(22):
            score += 4
            reasons.append(f"RSI={current_rsi:.0f} (خیلی بیش‌فروش)")
        elif current_rsi < Decimal(28):
            score += 3
            reasons.append(f"RSI={current_rsi:.0f} (بیش‌فروش شدید)")
        elif current_rsi < Decimal(32):
            score += 2
            reasons.append(f"RSI={current_rsi:.0f} (بیش‌فروش)")

    # ---------- ۲. RSI Divergence ----------
    # قیمت کف پایین‌تر زده ولی RSI کف بالاتر
    if len(window) >= 20:
        recent_prices = [c.close for c in window[-20:]]
        recent_rsi = [v for v in rsi_values[-20:] if v is not None]

        if len(recent_rsi) >= 10:
            # دو کف اخیر قیمت
            last_5_low = min(recent_prices[-5:])
            prev_5_low = min(recent_prices[-10:-5])

            if last_5_low < prev_5_low:  # قیمت کف پایین‌تر
                last_5_rsi_min = min(recent_rsi[-5:])
                prev_5_rsi_min = min(recent_rsi[-10:-5])
                if last_5_rsi_min > prev_5_rsi_min:  # RSI کف بالاتر
                    score += 2
                    reasons.append("Divergence (قیمت پایین‌تر، RSI بالاتر)")

    # ---------- ۳. Volume Spike ----------
    vol_ma_values = volume_sma(window, 20)
    current_vol_ma = _last(vol_ma_values)

    if current_vol_ma and current_vol_ma > 0:
        vol_ratio = current.volume / current_vol_ma
        # Volume فقط وقتی معنی‌داره که RSI هم Oversold باشه
        rsi_oversold = current_rsi is not None and current_rsi < Decimal(35)
        if rsi_oversold:
            if vol_ratio > Decimal("3"):
                score += 3
                reasons.append(f"حجم {vol_ratio:.1f}× + RSI پایین (Capitulation)")
            elif vol_ratio > Decimal("2"):
                score += 2
                reasons.append(f"حجم {vol_ratio:.1f}× + RSI پایین")
        else:
            # حجم بالا بدون RSI پایین = نویز
            if vol_ratio > Decimal("3"):
                score += 1
                reasons.append("حجم بالا (بدون RSI oversold)")

    # ---------- ۴. Rejection Wick ----------
    hl_range = current.high - current.low
    if hl_range > 0:
        body = abs(current.close - current.open)
        lower_wick = min(current.open, current.close) - current.low
        lower_wick_ratio = lower_wick / hl_range
        body_ratio = body / hl_range

        if lower_wick_ratio > Decimal("0.6") and body_ratio < Decimal("0.3"):
            score += 2
            reasons.append(f"سایه‌ی پایینی بلند ({lower_wick_ratio * 100:.0f}%)")
        elif lower_wick_ratio > Decimal("0.5"):
            score += 1
            reasons.append(f"سایه‌ی پایینی ({lower_wick_ratio * 100:.0f}%)")

    # ---------- ۵. Support Touch ----------
    if idx >= 50:
        swings = find_swing_levels(window[-100:], lookback=5, tolerance_pct=0.8)
        supports = [s for s in swings if s.type == "support"]

        for sup in supports:
            distance_pct = abs(current.low - sup.price) / sup.price * Decimal(100)
            if distance_pct < Decimal("0.5"):
                if sup.touches >= 3:
                    score += 3
                    reasons.append(f"لمس حمایت قوی ({sup.touches} بار)")
                elif sup.touches >= 2:
                    score += 2
                    reasons.append(f"لمس حمایت ({sup.touches} بار)")
                else:
                    score += 1
                    reasons.append("لمس حمایت ضعیف")
                break

    # ---------- ۶. فیلتر روند (CRITICAL) ----------
    from app.services.indicators import ema

    ema20_vals = ema(window, 20)
    ema50_vals = ema(window, 50)
    ema20 = _last(ema20_vals)
    ema50 = _last(ema50_vals)

    in_downtrend = False
    if ema20 and ema50 and ema20 < ema50:
        # چک کن چقدر زیره
        diff_pct = (ema50 - ema20) / ema50 * 100
        if diff_pct > Decimal(4):  # روند خیلی نزولی
            in_downtrend = True
            reasons.append("⚠️ روند نزولی قوی (EMA20 < EMA50)")

    # ---------- نتیجه ----------
    if in_downtrend:
        is_bottom = False
        strength = "none"
    elif score >= 8:
        strength = "strong"
        is_bottom = True
    elif score >= 6:
        strength = "medium"
        is_bottom = True
    elif score >= 4:
        strength = "weak"
        is_bottom = False
    else:
        strength = "none"
        is_bottom = False

    # جلوگیری از تشخیص تکراری (مگر حالت داخلی)
    if is_bottom and not _internal and _has_recent_bottom(candles, idx, hours=4):
        is_bottom = False
        strength = "none"
        reasons.append("❌ کف تکراری (اخیراً تشخیص داده شده)")

    return BottomSignal(
        is_bottom=is_bottom,
        score=score,
        strength=strength,
        reasons=reasons,
        price=current.close,
        time=current.time,
    )
