"""Trend Analyzer v2 — تحلیل روند با ۸ معیار متمایزکننده.

Trend Score: -100..+100
  - +100 = صعودی بسیار قوی
  - 0    = بدون روند
  - -100 = نزولی بسیار قوی
"""

from dataclasses import dataclass
from decimal import Decimal

from app.domain.entities.candle import Candle
from app.services.indicators import atr, ema, rsi, sma


@dataclass(slots=True)
class TrendResult:
    score: int
    direction: str
    strength: str
    pattern: str
    volatility_pct: Decimal
    ema_alignment: str
    reasons: list[str]


def _last(values):
    for v in reversed(values):
        if v is not None:
            return v
    return None


def analyze_trend(candles: list[Candle]) -> TrendResult:
    """تحلیل روند با ۸ معیار متمایز."""
    reasons: list[str] = []
    score = 0

    if len(candles) < 100:
        return TrendResult(
            score=0,
            direction="neutral",
            strength="weak",
            pattern="ranging",
            volatility_pct=Decimal(0),
            ema_alignment="mixed",
            reasons=["داده کافی نیست"],
        )

    ema20 = ema(candles, 20)
    ema50 = ema(candles, 50)
    sma100 = sma(candles, 100)
    atr14 = atr(candles, 14)
    rsi14 = rsi(candles, 14)

    last = candles[-1]
    last_close = last.close
    last_ema20 = _last(ema20)
    last_ema50 = _last(ema50)
    last_sma100 = _last(sma100)
    last_atr = _last(atr14)
    last_rsi = _last(rsi14)

    # ========== ۱. موقعیت قیمت (20 امتیاز) ==========
    if last_ema20 and last_ema20 > 0:
        diff_pct = ((last_close - last_ema20) / last_ema20) * 100
        if diff_pct > Decimal(5):
            score += 10
            reasons.append(f"قیمت {diff_pct:.1f}% بالای EMA(20) (اشباع)")
        elif diff_pct > Decimal(1):
            score += 15
            reasons.append(f"قیمت {diff_pct:.1f}% بالای EMA(20)")
        elif diff_pct > 0:
            score += 20
            reasons.append("قیمت نزدیک EMA(20) (صعودی)")
        elif diff_pct < Decimal(-5):
            score -= 15
            reasons.append(f"قیمت {abs(diff_pct):.1f}% زیر EMA(20)")
        elif diff_pct < 0:
            score -= 8
            reasons.append("قیمت زیر EMA(20)")

    # ========== ۲. EMA Cross (20 امتیاز) ==========
    if last_ema20 and last_ema50 and last_ema50 > 0:
        ema_diff_pct = ((last_ema20 - last_ema50) / last_ema50) * 100
        if ema_diff_pct > Decimal(3):
            score += 20
            reasons.append(f"EMA(20) بالای EMA(50) ({ema_diff_pct:.1f}%)")
        elif ema_diff_pct > Decimal("0.5"):
            score += 15
            reasons.append("EMA(20) > EMA(50)")
        elif ema_diff_pct > 0:
            score += 8
            reasons.append("EMA(20) کمی بالای EMA(50)")
        elif ema_diff_pct < Decimal(-3):
            score -= 20
            reasons.append(f"EMA(20) زیر EMA(50) ({ema_diff_pct:.1f}%)")
        elif ema_diff_pct < 0:
            score -= 8
            reasons.append("EMA(20) < EMA(50)")

    # ========== ۳. SMA100 روند بلندمدت (10 امتیاز) ==========
    if last_sma100 and last_sma100 > 0:
        if last_close > last_sma100:
            score += 10
            reasons.append("قیمت بالای SMA(100)")
        else:
            score -= 10
            reasons.append("قیمت زیر SMA(100)")

    # ========== ۴. شیب EMA(20) — قدرت روند (20 امتیاز) ==========
    ema20_values = [v for v in ema20 if v is not None]
    if len(ema20_values) >= 10:
        recent = ema20_values[-1]
        past = ema20_values[-10]
        if past != 0:
            slope_pct = ((recent - past) / past) * 100
            if slope_pct > Decimal(5):
                score += 20
                reasons.append(f"شیب EMA قوی ({slope_pct:.1f}%)")
            elif slope_pct > Decimal(1):
                score += 12
                reasons.append(f"شیب EMA صعودی ({slope_pct:.1f}%)")
            elif slope_pct > 0:
                score += 5
            elif slope_pct < Decimal(-5):
                score -= 20
                reasons.append("شیب EMA نزولی قوی")
            elif slope_pct < Decimal(-1):
                score -= 12
            elif slope_pct < 0:
                score -= 5

    # ========== ۵. RSI — اشباع (20 امتیاز) ==========
    if last_rsi is not None:
        if last_rsi > Decimal(80):
            score -= 15
            reasons.append(f"RSI = {last_rsi:.0f} (بیش‌خرید شدید)")
        elif last_rsi > Decimal(70):
            score -= 8
            reasons.append(f"RSI = {last_rsi:.0f} (بیش‌خرید)")
        elif last_rsi > Decimal(55):
            score += 12
            reasons.append(f"RSI = {last_rsi:.0f} (مومنتوم مثبت)")
        elif last_rsi > Decimal(45):
            score += 5
            reasons.append(f"RSI = {last_rsi:.0f} (متعادل)")
        elif last_rsi > Decimal(30):
            score -= 5
            reasons.append(f"RSI = {last_rsi:.0f} (ضعیف)")
        else:
            score += 10
            reasons.append(f"RSI = {last_rsi:.0f} (بیش‌فروش — فرصت)")

    # ========== ۶. Momentum — بازده اخیر (15 امتیاز) ==========
    if len(candles) >= 20:
        ret_20 = ((candles[-1].close - candles[-20].close) / candles[-20].close) * 100
        if ret_20 > Decimal(20):
            score -= 10
            reasons.append(f"بازده ۲۰ کندل +{ret_20:.1f}% (خسته)")
        elif ret_20 > Decimal(5):
            score += 15
            reasons.append(f"مومنتوم قوی (+{ret_20:.1f}%)")
        elif ret_20 > 0:
            score += 8
        elif ret_20 < Decimal(-20):
            score += 10
            reasons.append(f"افت شدید ({ret_20:.1f}%) — فرصت بازگشت")
        elif ret_20 < Decimal(-5):
            score -= 15
            reasons.append(f"مومنتوم نزولی ({ret_20:.1f}%)")
        elif ret_20 < 0:
            score -= 8

    # ========== ۷. فاصله از سقف (10 امتیاز) ==========
    if len(candles) >= 50:
        recent_high = max(c.high for c in candles[-50:])
        recent_low = min(c.low for c in candles[-50:])
        range_size = recent_high - recent_low
        if range_size > 0:
            position = (last_close - recent_low) / range_size
            if position > Decimal("0.9"):
                score -= 5
                reasons.append("نزدیک سقف ۵۰ کندل (احتیاط)")
            elif position > Decimal("0.6"):
                score += 8
                reasons.append("در نیمه‌ی بالایی بازه")
            elif position > Decimal("0.3"):
                score += 3
            else:
                score += 10
                reasons.append("نزدیک کف بازه (فرصت)")

    # ========== ۸. فاصله ATR (5 امتیاز) ==========
    if last_atr and last_close > 0:
        atr_pct = (last_atr / last_close) * 100
        if atr_pct < Decimal(1):
            score += 5
            reasons.append("نوسان کم — روند پایدار")
        elif atr_pct > Decimal(6):
            score -= 5
            reasons.append("نوسان بالا — عدم قطعیت")

    # clamp
    score = max(-100, min(100, score))

    # جهت — آستانه‌های واقع‌بینانه
    if score >= 70:
        direction, strength = "bullish", "strong"
    elif score >= 40:
        direction, strength = "bullish", "medium"
    elif score >= 15:
        direction, strength = "bullish", "weak"
    elif score <= -70:
        direction, strength = "bearish", "strong"
    elif score <= -40:
        direction, strength = "bearish", "medium"
    elif score <= -15:
        direction, strength = "bearish", "weak"
    else:
        direction, strength = "neutral", "weak"

    # نوسان
    if last_atr and last_close > 0:
        raw_vol = (last_atr / last_close) * 100
        volatility_pct = min(raw_vol, Decimal(10))
    else:
        volatility_pct = Decimal(0)

    # الگو
    if abs(score) >= 40:
        pattern = "trending"
    elif volatility_pct > Decimal(3):
        pattern = "choppy"
    else:
        pattern = "ranging"

    # EMA alignment
    if last_ema20 and last_ema50 and last_sma100:
        if last_ema20 > last_ema50 > last_sma100 or last_ema20 < last_ema50 < last_sma100:
            ema_alignment = "aligned"
        else:
            ema_alignment = "mixed"
    else:
        ema_alignment = "counter"

    return TrendResult(
        score=score,
        direction=direction,
        strength=strength,
        pattern=pattern,
        volatility_pct=volatility_pct,
        ema_alignment=ema_alignment,
        reasons=reasons,
    )
