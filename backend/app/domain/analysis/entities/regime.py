"""Regime — طبقه‌بندی لحظه‌ای بازار.

۴ regime (مطابق regime_detector موجود):
  trending_up, trending_down, ranging, choppy
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class RegimeType(StrEnum):
    """انواع regime بازار."""

    TRENDING_UP = "trending_up"
    TRENDING_DOWN = "trending_down"
    RANGING = "ranging"
    CHOPPY = "choppy"


@dataclass(frozen=True, slots=True)
class RegimeResult:
    """خروجی طبقه‌بندی یه پنجره."""

    regime: RegimeType
    confidence: int
    reasons: tuple[str, ...]
    is_tradeable: bool
    adx: float = 0.0
    atr_pct: float = 0.0
    ema_alignment: str = "mixed"
