"""Regime Detector — تشخیص فاز بازار.

چهار رژیم:
  - trending_up:   روند صعودی قوی
  - trending_down: روند نزولی قوی
  - ranging:       در محدوده (نوسان کم)
  - choppy:        پرنوسان بدون جهت

معیارها:
  - ADX (قدرت روند)
  - ATR% (نوسان)
  - EMA alignment
  - بازده تجمعی
"""

from dataclasses import dataclass
from enum import StrEnum

from app.domain.entities.candle import Candle
from app.services.indicators import atr, ema


class RegimeType(StrEnum):
    TRENDING_UP = "trending_up"
    TRENDING_DOWN = "trending_down"
    RANGING = "ranging"
    CHOPPY = "choppy"


@dataclass(slots=True)
class RegimeResult:
    regime: RegimeType
    confidence: int  # 0-100
    adx: float  # قدرت روند
    atr_pct: float  # نوسان
    ema_alignment: str  # aligned_up/down/mixed
    reasons: list[str]
    # برای اینکه بتونیم در استراتژی ازش استفاده کنیم
    is_tradeable: bool  # آیا این رژیم برای ترید مناسبه؟


def _last(values):
    for v in reversed(values):
        if v is not None:
            return v
    return None


def calculate_adx(candles: list[Candle], period: int = 14) -> float | None:
    """محاسبه‌ی ADX — قدرت روند."""
    if len(candles) < period + 1:
        return None

    trs = []
    plus_dm = []
    minus_dm = []

    for i in range(1, len(candles)):
        high = float(candles[i].high)
        low = float(candles[i].low)
        prev_high = float(candles[i - 1].high)
        prev_low = float(candles[i - 1].low)
        prev_close = float(candles[i - 1].close)

        tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
        trs.append(tr)

        up_move = high - prev_high
        down_move = prev_low - low

        plus_dm.append(up_move if up_move > down_move and up_move > 0 else 0)
        minus_dm.append(down_move if down_move > up_move and down_move > 0 else 0)

    if len(trs) < period:
        return None

    # میانگین‌های Wilder
    atr_val = sum(trs[:period]) / period
    plus_di_avg = sum(plus_dm[:period]) / period
    minus_di_avg = sum(minus_dm[:period]) / period

    dx_values = []
    for i in range(period, len(trs)):
        atr_val = (atr_val * (period - 1) + trs[i]) / period
        plus_di_avg = (plus_di_avg * (period - 1) + plus_dm[i]) / period
        minus_di_avg = (minus_di_avg * (period - 1) + minus_dm[i]) / period

        if atr_val == 0:
            continue

        plus_di = 100 * plus_di_avg / atr_val
        minus_di = 100 * minus_di_avg / atr_val

        di_sum = plus_di + minus_di
        if di_sum == 0:
            continue

        dx = 100 * abs(plus_di - minus_di) / di_sum
        dx_values.append(dx)

    if not dx_values:
        return None

    # ADX = میانگین DX
    adx_val = sum(dx_values[-period:]) / min(period, len(dx_values))
    return adx_val


def detect_regime(candles: list[Candle]) -> RegimeResult:
    """تشخیص رژیم بازار."""
    if len(candles) < 50:
        return RegimeResult(
            regime=RegimeType.RANGING,
            confidence=0,
            adx=0,
            atr_pct=0,
            ema_alignment="mixed",
            reasons=["داده کافی نیست"],
            is_tradeable=False,
        )

    reasons: list[str] = []
    current = candles[-1]

    # ---------- ۱. ADX ----------
    adx = calculate_adx(candles, 14) or 0

    # ---------- ۲. ATR% ----------
    atr14 = _last(atr(candles, 14))
    atr_pct = float(atr14 / current.close * 100) if atr14 else 0

    # ---------- ۳. EMA Alignment ----------
    ema20 = _last(ema(candles, 20))
    ema50 = _last(ema(candles, 50))
    ema100 = _last(ema(candles, 100)) if len(candles) >= 100 else None

    ema_alignment = "mixed"
    if ema20 and ema50:
        if ema100:
            if ema20 > ema50 > ema100:
                ema_alignment = "aligned_up"
                reasons.append("EMA(20)>EMA(50)>EMA(100)")
            elif ema20 < ema50 < ema100:
                ema_alignment = "aligned_down"
                reasons.append("EMA(20)<EMA(50)<EMA(100)")
            else:
                ema_alignment = "mixed"
        elif ema20 > ema50:
            ema_alignment = "aligned_up"
        elif ema20 < ema50:
            ema_alignment = "aligned_down"

    # ---------- ۴. بازده تجمعی ----------
    ret_20 = (
        float((candles[-1].close - candles[-21].close) / candles[-21].close * 100)
        if len(candles) >= 21
        else 0
    )

    # ---------- تصمیم ----------
    # منطق جدید:
    #   ADX بالا (>=25) + ret_20 قوی (>=3%) = trending
    #   ADX بالا (>=25) + ret_20 ضعیف = choppy (نوسان بدون جهت)
    #   ADX پایین (<20) = ranging (آرام)
    #   ADX متوسط = انتقالی (بسته به ATR)

    regime = RegimeType.RANGING
    confidence = 50

    # کالیبره شده برای 1h crypto:
    #   ADX >= 25 + EMA aligned + ret_20 هم‌جهت → trending
    #   ADX >= 25 ولی EMA mixed و ret کم → choppy
    #   ADX < 20 + ATR بالا → choppy
    #   ADX < 20 + ATR پایین → ranging
    #   ADX 20-25 → transitional

    ema_up = ema_alignment == "aligned_up"
    ema_down = ema_alignment == "aligned_down"
    ema_mixed = ema_alignment == "mixed"

    if adx >= 25:
        # روند قوی — آستانه‌ی بازده رو آوردیم پایین
        if ret_20 >= 1.0 and (ema_up or (ema_mixed and ret_20 >= 2.0)):
            regime = RegimeType.TRENDING_UP
            confidence = min(95, 55 + int(adx * 0.8))
            reasons.insert(0, f"ADX={adx:.0f} + بازده +{ret_20:.1f}% + EMA↑")
        elif ret_20 <= -1.0 and (ema_down or (ema_mixed and ret_20 <= -2.0)):
            regime = RegimeType.TRENDING_DOWN
            confidence = min(95, 55 + int(adx * 0.8))
            reasons.insert(0, f"ADX={adx:.0f} + بازده {ret_20:.1f}% + EMA↓")
        elif abs(ret_20) < 0.8:
            # ADX بالا ولی بدون حرکت — واقعاً choppy
            regime = RegimeType.CHOPPY
            confidence = min(80, 50 + int(adx * 0.6))
            reasons.insert(0, f"ADX={adx:.0f} ولی بدون جهت (ret={ret_20:+.1f}%)")
        else:
            # بین 0.8 تا 1.0 — مرزی، به EMA رجوع
            if ema_up and ret_20 > 0:
                regime = RegimeType.TRENDING_UP
                confidence = 65
                reasons.insert(0, f"ADX={adx:.0f} + EMA↑ (مرزی)")
            elif ema_down and ret_20 < 0:
                regime = RegimeType.TRENDING_DOWN
                confidence = 65
                reasons.insert(0, f"ADX={adx:.0f} + EMA↓ (مرزی)")
            else:
                regime = RegimeType.CHOPPY
                confidence = 55
                reasons.insert(0, "سیگنال‌های متناقض")

    elif adx < 20:
        # بدون روند
        if atr_pct > 1.5:
            # نوسان بالا بدون جهت = choppy
            regime = RegimeType.CHOPPY
            confidence = min(85, 50 + int(atr_pct * 12))
            reasons.insert(0, f"ADX={adx:.0f} پایین + ATR={atr_pct:.2f}% بالا")
        else:
            # آرام = ranging
            regime = RegimeType.RANGING
            confidence = min(90, 60 + int(20 - adx))
            reasons.insert(0, f"ADX={adx:.0f} + ATR={atr_pct:.2f}% (آرام)")

    else:
        # ADX 20-25 → transitional
        if atr_pct > 2.5:
            regime = RegimeType.CHOPPY
            confidence = 55
            reasons.insert(0, f"ADX={adx:.0f} + ATR={atr_pct:.1f}% بالا")
        elif ema_up and ret_20 >= 1.5:
            regime = RegimeType.TRENDING_UP
            confidence = 60
            reasons.insert(0, f"ADX={adx:.0f} + EMA↑ (شروع روند)")
        elif ema_down and ret_20 <= -1.5:
            regime = RegimeType.TRENDING_DOWN
            confidence = 60
            reasons.insert(0, f"ADX={adx:.0f} + EMA↓ (شروع روند)")
        else:
            regime = RegimeType.RANGING
            confidence = 55
            reasons.insert(0, f"ADX={adx:.0f} (گذار)")

    # آیا قابل تریده؟
    # در روند صعودی: بله (فقط خرید)
    # در روند نزولی: نه
    # در رنج: بله (کف‌خرید، سقف‌فروش)
    # در پرنوسان: نه
    is_tradeable = regime in (RegimeType.TRENDING_UP, RegimeType.RANGING)

    return RegimeResult(
        regime=regime,
        confidence=confidence,
        adx=round(adx, 1),
        atr_pct=round(atr_pct, 2),
        ema_alignment=ema_alignment,
        reasons=reasons,
        is_tradeable=is_tradeable,
    )
