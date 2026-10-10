"""RuleBasedClassifier — پیاده‌سازی RegimeClassifierPort.

منتقل‌شده از services/regime_detector.py با دو تغییر:
  - از feature_math استفاده می‌کنه (float، نه services/indicators)
  - RegimeResult از domain/analysis/entities/regime میاد

منطق: ADX + ATR% + EMA alignment + ret_20
"""

from __future__ import annotations

from typing import Sequence

from app.domain.analysis.entities.regime import RegimeResult, RegimeType
from app.domain.analysis.models.feature_math import atr_last, adx, ema_last
from app.domain.entities.candle import Candle


def _ret_pct(candles: Sequence[Candle], n: int) -> float:
    if len(candles) < n + 1:
        return 0.0
    a = float(candles[-1].close)
    b = float(candles[-1 - n].close)
    return (a - b) / b * 100 if b else 0.0


class RuleBasedClassifier:
    """طبقه‌بندی regime با قوانین ADX/ATR/EMA — کالیبره برای 1h crypto."""

    def classify(self, candles: Sequence[Candle]) -> RegimeResult:
        if len(candles) < 50:
            return RegimeResult(
                regime=RegimeType.RANGING,
                confidence=0,
                reasons=("داده کافی نیست",),
                is_tradeable=False,
            )

        reasons: list[str] = []
        current_close = float(candles[-1].close)

        a = adx(candles, 14)
        atr_v = atr_last(candles, 14)
        atr_pct = (atr_v / current_close * 100) if current_close else 0.0

        ema20 = ema_last(candles, 20)
        ema50 = ema_last(candles, 50)
        ema100 = ema_last(candles, 100) if len(candles) >= 100 else 0.0

        alignment = "mixed"
        if ema20 and ema50:
            if ema100 and ema20 > ema50 > ema100:
                alignment = "aligned_up"
                reasons.append("EMA(20)>EMA(50)>EMA(100)")
            elif ema100 and ema20 < ema50 < ema100:
                alignment = "aligned_down"
                reasons.append("EMA(20)<EMA(50)<EMA(100)")
            elif not ema100 and ema20 > ema50:
                alignment = "aligned_up"
            elif not ema100 and ema20 < ema50:
                alignment = "aligned_down"

        ret_20 = _ret_pct(candles, 20)
        ema_up = alignment == "aligned_up"
        ema_down = alignment == "aligned_down"

        regime = RegimeType.RANGING
        confidence = 50

        if a >= 25:
            if ret_20 >= 1.0 and ema_up:
                regime = RegimeType.TRENDING_UP
                confidence = min(95, 55 + int(a * 0.8))
                reasons.insert(0, f"ADX={a:.0f} + بازده +{ret_20:.1f}% + EMA↑")
            elif ret_20 <= -1.0 and ema_down:
                regime = RegimeType.TRENDING_DOWN
                confidence = min(95, 55 + int(a * 0.8))
                reasons.insert(0, f"ADX={a:.0f} + بازده {ret_20:.1f}% + EMA↓")
            elif abs(ret_20) < 0.8:
                regime = RegimeType.CHOPPY
                confidence = min(80, 50 + int(a * 0.6))
                reasons.insert(0, f"ADX={a:.0f} ولی بدون جهت")
            else:
                regime = RegimeType.CHOPPY
                confidence = 55
                reasons.insert(0, "سیگنال‌های متناقض")
        elif a < 20:
            if atr_pct > 1.5:
                regime = RegimeType.CHOPPY
                confidence = min(85, 50 + int(atr_pct * 12))
                reasons.insert(0, f"ADX={a:.0f} + ATR={atr_pct:.2f}% بالا")
            else:
                regime = RegimeType.RANGING
                confidence = min(90, 60 + int(20 - a))
                reasons.insert(0, f"ADX={a:.0f} + ATR={atr_pct:.2f}% (آرام)")
        else:
            if atr_pct > 2.5:
                regime = RegimeType.CHOPPY
                confidence = 55
                reasons.insert(0, f"ADX={a:.0f} + ATR={atr_pct:.1f}% بالا")
            elif ema_up and ret_20 >= 1.5:
                regime = RegimeType.TRENDING_UP
                confidence = 60
                reasons.insert(0, f"ADX={a:.0f} + EMA↑")
            elif ema_down and ret_20 <= -1.5:
                regime = RegimeType.TRENDING_DOWN
                confidence = 60
                reasons.insert(0, f"ADX={a:.0f} + EMA↓")
            else:
                regime = RegimeType.RANGING
                confidence = 55
                reasons.insert(0, f"ADX={a:.0f} (گذار)")

        is_tradeable = regime in (RegimeType.TRENDING_UP, RegimeType.RANGING)

        return RegimeResult(
            regime=regime,
            confidence=confidence,
            reasons=tuple(reasons),
            is_tradeable=is_tradeable,
            adx=round(a, 1),
            atr_pct=round(atr_pct, 2),
            ema_alignment=alignment,
        )
