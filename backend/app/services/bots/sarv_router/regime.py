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


def detect_regime(candles: list[Candle], config: SarvRouterConfig, warmup: int | None = None) -> Regime:
    """Classify regime. Optional `warmup` overrides config.warmup_candles (for 4h)."""
    w = warmup if warmup is not None else config.warmup_candles
    if len(candles) < w:
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


def detect_regime_multi_tf(candles_1h: list[Candle], config: SarvRouterConfig) -> Regime:
    """Multi-TF: 1h AND 4h must agree. Disagreement → UNKNOWN."""
    from app.services.bots.sarv_router.resample import resample_4h

    r1h = detect_regime(candles_1h, config)
    if r1h == Regime.UNKNOWN:
        return Regime.UNKNOWN

    c4h = resample_4h(candles_1h)
    r4h = detect_regime(c4h, config, warmup=config.ema_period + 5)

    if r1h == r4h:
        return r1h
    return Regime.UNKNOWN
