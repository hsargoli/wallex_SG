"""ScannedSymbol — نماد اسکن‌شده با امتیاز نوسان."""

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class VolatilityScore:
    """امتیاز نوسان یک نماد (Value Object)."""

    total: float  # 0-100
    atr_pct: float
    std_returns: float
    range_pct: float
    volume_ratio: float


@dataclass(frozen=True, slots=True)
class ScannedSymbol:
    """نماد اسکن‌شده با اطلاعات کامل."""

    symbol: str
    current_price: Decimal
    score: VolatilityScore
    volume_24h: Decimal | None = None
    change_24h: Decimal | None = None
    timeframe: str = "1h"
    scanned_at: int = 0
