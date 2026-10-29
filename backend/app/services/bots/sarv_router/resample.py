"""Resample 1h candles to higher timeframes."""
from decimal import Decimal
from app.domain.entities.candle import Candle


def resample_4h(candles_1h: list[Candle]) -> list[Candle]:
    """Aggregate consecutive 4 x 1h candles into one 4h candle.

    Drops incomplete tail (if len % 4 != 0).
    """
    out: list[Candle] = []
    for i in range(0, len(candles_1h), 4):
        chunk = candles_1h[i:i + 4]
        if len(chunk) < 4:
            break
        out.append(Candle(
            time=chunk[0].time,
            open=chunk[0].open,
            high=max(c.high for c in chunk),
            low=min(c.low for c in chunk),
            close=chunk[-1].close,
            volume=sum((c.volume for c in chunk), Decimal("0")),
        ))
    return out
