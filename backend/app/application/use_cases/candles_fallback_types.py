"""Types for candles-with-fallback use case."""

from dataclasses import dataclass, field

from app.domain.entities.candle import Candle


@dataclass(slots=True)
class SyntheticRange:
    """بازه‌ای که از تایم‌فریم بالاتر شبیه‌سازی شده."""

    from_ts: int  # شروع بازه (ثانیه)
    to_ts: int  # پایان بازه (ثانیه)
    source_tf: str  # تایم‌فریم منبع (1D, 1h)


@dataclass(slots=True)
class CandlesWithFallback:
    """نتیجه‌ی دریافت کندل با شبیه‌سازی fallback."""

    candles: list[Candle] = field(default_factory=list)
    synthetic_ranges: list[SyntheticRange] = field(default_factory=list)
    requested_tf: str = ""
    applied_limit: int = 0
    real_candles_count: int = 0
    synthetic_candles_count: int = 0
