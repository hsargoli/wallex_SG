"""PersonalityStats — آمار «شخصیت» یه ارز در یه بازه.

مثلاً: «BTC در ۳۰ روز، ۵ بار سقوط، ۱۲ نزول،
۲۰ دوره آروم — میانگین نوسان ۲.۱٪».
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class PersonalityStats:
    """خلاصه‌ی آماری رفتار یه ارز."""

    symbol: str
    timeframe: str
    window_count: int
    regime_counts: dict[str, int] = field(default_factory=dict)
    volatility_mean: float = 0.0
    volatility_std: float = 0.0
    rsi_mean: float = 0.0
    trend_mean: float = 0.0

    @property
    def dominant_regime(self) -> str | None:
        """regime غالب (بیشترین فراوانی)."""
        if not self.regime_counts:
            return None
        return max(self.regime_counts, key=lambda k: self.regime_counts[k])
