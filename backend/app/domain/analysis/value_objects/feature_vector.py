"""FeatureVector — بردار feature برای یه پنجره‌ی زمانی."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class FeatureVector:
    """۴ feature اصلی برای یه پنجره.

    - volatility: نوسان (std pct_change × 100)
    - rsi: 0-100 (اشباع خرید/فروش)
    - trend_strength: شیب رگرسیون نرمالایز (%)
    - volume_z: z-score آخرین حجم نسبت به پنجره
    """

    volatility: float
    rsi: float
    trend_strength: float
    volume_z: float

    def as_tuple(self) -> tuple[float, float, float, float]:
        """بردار عددی — برای KMeans."""
        return (self.volatility, self.rsi, self.trend_strength, self.volume_z)

    @property
    def dim(self) -> int:
        return 4
