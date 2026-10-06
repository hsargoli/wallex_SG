"""تنظیمات Market Scanner Bot."""

from dataclasses import dataclass


@dataclass(slots=True)
class MarketScannerConfig:
    """تنظیمات اسکنر بازار."""

    # تایم‌فریم
    timeframe: str = "1h"
    available_timeframes: list[str] = None

    def __post_init__(self):
        if self.available_timeframes is None:
            self.available_timeframes = ["15m", "1h", "4h", "1D"]

    # اسکن
    quote: str = "TMN"
    top_n: int = 100
    min_score: float = 0.0
    max_concurrent: int = 15

    # بازه اسکن
    scan_interval_sec: int = 300  # ۵ دقیقه

    # ذخیره
    save_results: bool = True
