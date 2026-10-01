"""استراتژی Trend Follow — ورود با Golden Cross + ADX."""

from dataclasses import dataclass
from decimal import Decimal

from app.domain.entities.candle import Candle
from app.services.bots.trend_follow.config import TrendFollowConfig
from app.services.indicators import atr, ema, volume_sma


@dataclass(slots=True)
class TrendSignal:
    should_enter: bool
    entry_price: float
    initial_sl: float
    trailing_distance: float
    reason: str
    confidence: int
    adx: float


@dataclass(slots=True)
class TrendExit:
    should_exit: bool
    new_sl: float | None
    reason: str


def _last(values):
    for v in reversed(values):
        if v is not None:
            return v
    return None


def _prev(values):
    found = 0
    for v in reversed(values):
        if v is not None:
            found += 1
            if found == 2:
                return v
    return None


def _calc_adx(candles: list[Candle], period: int = 14) -> float:
    if len(candles) < period + 2:
        return 0.0
    trs, plus_dm, minus_dm = [], [], []
    for i in range(1, len(candles)):
        h = float(candles[i].high)
        l = float(candles[i].low)
        ph = float(candles[i - 1].high)
        pl = float(candles[i - 1].low)
        pc = float(candles[i - 1].close)
        tr = max(h - l, abs(h - pc), abs(l - pc))
        trs.append(tr)
        up = h - ph
        dn = pl - l
        plus_dm.append(up if up > dn and up > 0 else 0)
        minus_dm.append(dn if dn > up and dn > 0 else 0)
    if len(trs) < period:
        return 0.0
    atr_v = sum(trs[:period]) / period
    p_avg = sum(plus_dm[:period]) / period
    m_avg = sum(minus_dm[:period]) / period
    dx_vals = []
    for i in range(period, len(trs)):
        atr_v = (atr_v * (period - 1) + trs[i]) / period
        p_avg = (p_avg * (period - 1) + plus_dm[i]) / period
        m_avg = (m_avg * (period - 1) + minus_dm[i]) / period
        if atr_v == 0:
            continue
        pdi = 100 * p_avg / atr_v
        mdi = 100 * m_avg / atr_v
        s = pdi + mdi
        if s > 0:
            dx_vals.append(100 * abs(pdi - mdi) / s)
    if not dx_vals:
        return 0.0
    return sum(dx_vals[-period:]) / min(period, len(dx_vals))


def evaluate_entry(candles: list[Candle], config: TrendFollowConfig) -> TrendSignal | None:
    if len(candles) < config.warmup_candles:
        return None

    ema_fast = ema(candles, config.ema_fast)
    ema_slow = ema(candles, config.ema_slow)
    curr_fast = _last(ema_fast)
    curr_slow = _last(ema_slow)
    prev_fast = _prev(ema_fast)
    prev_slow = _prev(ema_slow)

    if not all([curr_fast, curr_slow, prev_fast, prev_slow]):
        return None

    # چک cross در N کندل آخر
    lookback = getattr(config, "cross_lookback", 3)
    golden_cross = False
    for i in range(1, lookback + 1):
        f_i = ema_fast[-i] if i <= len(ema_fast) else None
        s_i = ema_slow[-i] if i <= len(ema_slow) else None
        f_prev = ema_fast[-i - 1] if i + 1 <= len(ema_fast) else None
        s_prev = ema_slow[-i - 1] if i + 1 <= len(ema_slow) else None
        if all([f_i, s_i, f_prev, s_prev]):
            if f_prev <= s_prev and f_i > s_i:
                golden_cross = True
                break

    if not golden_cross:
        return None

    adx_val = _calc_adx(candles, config.adx_period)
    if adx_val < config.adx_threshold:
        return None

    vol_ma = volume_sma(candles, 20)
    cvm = _last(vol_ma)
    if cvm and cvm > 0:
        if candles[-1].volume / cvm < Decimal("1.0"):
            return None

    atr_vals = atr(candles, 14)
    c_atr = _last(atr_vals)
    if c_atr is None or c_atr <= 0:
        return None

    entry = float(candles[-1].close)
    atr_f = float(c_atr)
    initial_sl = entry - (config.sl_atr_mult * atr_f)
    trailing_dist = config.trail_atr_mult * atr_f
    confidence = min(95, 50 + int(adx_val * 1.5))

    return TrendSignal(
        should_enter=True,
        entry_price=entry,
        initial_sl=initial_sl,
        trailing_distance=trailing_dist,
        reason=f"Golden Cross + ADX={adx_val:.0f}",
        confidence=confidence,
        adx=adx_val,
    )


def evaluate_exit(
    candles: list[Candle],
    entry_price: float,
    current_sl: float,
    trailing_distance: float,
    config: TrendFollowConfig,
    candles_in_position: int,
) -> TrendExit:
    if not candles:
        return TrendExit(should_exit=False, new_sl=None, reason="")

    current = candles[-1]
    high = float(current.high)
    low = float(current.low)

    if low <= current_sl:
        reason = "trailing_sl" if current_sl > entry_price else "initial_sl"
        return TrendExit(should_exit=True, new_sl=None, reason=reason)

    new_sl = current_sl
    if config.use_trailing and high > entry_price:
        candidate = high - trailing_distance
        if candidate > new_sl:
            new_sl = candidate

    ema_fast = ema(candles, config.ema_fast)
    ema_slow = ema(candles, config.ema_slow)
    cf, cs = _last(ema_fast), _last(ema_slow)
    pf, ps = _prev(ema_fast), _prev(ema_slow)
    if all([cf, cs, pf, ps]):
        if pf >= ps and cf < cs:
            return TrendExit(should_exit=True, new_sl=None, reason="reverse_cross")

    if candles_in_position >= config.max_duration_candles:
        return TrendExit(should_exit=True, new_sl=None, reason="timeout")

    return TrendExit(should_exit=False, new_sl=new_sl, reason="")
