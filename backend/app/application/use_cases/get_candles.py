"""UseCase: دریافت کندل‌های تاریخی برای یک نماد."""

import time
from dataclasses import dataclass

from app.domain.entities.candle import Candle
from app.domain.ports.exchange import ExchangePort

# نگاشت تایم‌فریم‌های کاربر → (resolution والکس، تعداد کندل پایه، ثانیه)
TIMEFRAME_MAP: dict[str, tuple[str, int, int]] = {
    "15m": ("15", 15, 15 * 60),  # ۱۵ تا ۱ دقیقه‌ای
    "1h": ("60", 1, 60 * 60),  # مستقیم از والکس
    "4h": ("60", 4, 4 * 60 * 60),  # ۴ تا ۱ ساعته
    "1D": ("D", 1, 24 * 60 * 60),  # مستقیم از والکس
}

VALID_TIMEFRAMES = tuple(TIMEFRAME_MAP.keys())

# برای اطمینان، حداکثر کندل پایه که می‌گیریم
MAX_BASE_CANDLES = 5000


@dataclass(slots=True)
class GetCandlesUseCase:
    exchange: ExchangePort

    async def execute(
        self,
        symbol: str,
        timeframe: str,
        limit: int = 500,
    ) -> list[Candle]:
        """دریافت آخرین `limit` کندل برای نماد و تایم‌فریم داده‌شده."""
        if timeframe not in TIMEFRAME_MAP:
            raise ValueError(
                f"Unsupported timeframe '{timeframe}'. Valid: {', '.join(VALID_TIMEFRAMES)}"
            )
        if limit <= 0 or limit > 1000:
            raise ValueError("limit must be between 1 and 1000")

        resolution, factor, seconds_per_candle = TIMEFRAME_MAP[timeframe]

        # تعداد کندل پایه‌ای که باید از والکس بگیریم
        needed_base = limit * factor
        needed_base = min(needed_base, MAX_BASE_CANDLES)

        now = int(time.time())
        from_ts = now - needed_base * seconds_per_candle // factor

        # برای اطمینان، ۱۰٪ حاشیه اضافه می‌کنیم
        from_ts = int(from_ts - (now - from_ts) * 0.1)

        raw_candles = await self.exchange.get_candles(
            symbol=symbol,
            resolution=resolution,
            from_ts=from_ts,
            to_ts=now,
        )

        # اگه لازم بود، ادغام کن
        if factor > 1:
            from app.services.candle_aggregator import aggregate_candles

            candles = aggregate_candles(raw_candles, factor=factor)
        else:
            candles = raw_candles

        # آخرین limit کندل رو برگردون
        return candles[-limit:]
