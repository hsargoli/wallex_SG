"""RegimeDetector — ADX + EMA50 based market regime detection."""
from enum import StrEnum

from app.domain.entities.candle import Candle
from app.services.bots.sarv_router.config import SarvRouterConfig
from app.services.indicators import adx, ema


class Regime(StrEnum):
    UPTREND = "uptrend"
    DOWNTREND = "downtrend"
    RANGE = "range"
    UNKNOWN = "unknown"


def _last(values):
    for v in reversed(values):
        if v is not None:
            return v
    return None


def detect_regime(candles: list[Candle], config: SarvRouterConfig) -> Regime:
    """Classify current regime from last N candles.

    Rules:
      - adx > uptrend_adx_min and price > EMA50 → UPTREND
      - adx > downtrend_adx_min and price < EMA50 → DOWNTREND
      - adx < range_adx_max → RANGE
      - else (20 <= adx <= 25) → UNKNOWN
    """
    if len(candles) < config.warmup_candles:
        return Regime.UNKNOWN

    adx_vals = adx(candles, config.adx_period)
    ema_vals = ema(candles, config.ema_period)
    adx_now = _last(adx_vals)
    ema_now = _last(ema_vals)

    if adx_now is None or ema_now is None:
        return Regime.UNKNOWN

    adx_f = float(adx_now)
    ema_f = float(ema_now)
    if ema_f <= 0:
        return Regime.UNKNOWN
    price = float(candles[-1].close)

    if adx_f > config.uptrend_adx_min and price > ema_f:
        return Regime.UPTREND
    if adx_f > config.downtrend_adx_min and price < ema_f:
        return Regime.DOWNTREND
    if adx_f < config.range_adx_max:
        return Regime.RANGE
    return Regime.UNKNOWN
