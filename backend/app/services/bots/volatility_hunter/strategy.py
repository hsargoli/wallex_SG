"""استراتژی Volatility Hunter.

منطق:
  ۱. تشخیص ولتیلیتی بالا
  ۲. کشف range (کف و سقف)
  ۳. خرید در منطقه‌ی خرید (نزدیک کف)
  ۴. فروش در منطقه‌ی فروش (نزدیک سقف)
  ۵. خروج سریع اگه range شکست
"""

from dataclasses import dataclass

from app.domain.entities.candle import Candle
from app.services.bots.volatility_hunter.config import VolatilityHunterConfig
from app.services.indicators import atr


@dataclass(slots=True)
class RangeInfo:
    """اطلاعات محدوده."""

    is_valid: bool
    low: float
    high: float
    mid: float
    range_pct: float
    atr_pct: float
    position_in_range: float  # 0 = کف، 1 = سقف


@dataclass(slots=True)
class VolatilitySignal:
    """سیگنال ورود/خروج."""

    should_trade: bool
    action: str  # "buy" | "sell" | "hold"
    entry_price: float
    stop_loss: float
    take_profit: float
    reason: str
    confidence: int
    range_info: RangeInfo | None = None


def _last(v):
    for x in reversed(v):
        if x is not None:
            return x
    return None


def detect_range(
    candles: list[Candle],
    config: VolatilityHunterConfig,
) -> RangeInfo:
    """کشف محدوده‌ی نوسان."""
    if len(candles) < config.lookback_candles:
        return RangeInfo(False, 0, 0, 0, 0, 0, 0)

    recent = candles[-config.lookback_candles :]
    current = candles[-1]

    # سقف و کف اخیر
    highs = [float(c.high) for c in recent]
    lows = [float(c.low) for c in recent]
    high = max(highs)
    low = min(lows)

    if low <= 0:
        return RangeInfo(False, 0, 0, 0, 0, 0, 0)

    range_pct = (high - low) / low * 100
    mid = (high + low) / 2

    # ATR%
    atr_vals = atr(candles, 14)
    atr_v = _last(atr_vals)
    atr_pct = float(atr_v) / float(current.close) * 100 if atr_v else 0

    # موقعیت در range
    price = float(current.close)
    if high > low:
        pos = (price - low) / (high - low)
    else:
        pos = 0.5

    # ولید بودن
    is_valid = (
        config.min_range_pct <= range_pct <= config.max_range_pct and atr_pct >= config.min_atr_pct
    )

    return RangeInfo(
        is_valid=is_valid,
        low=low,
        high=high,
        mid=mid,
        range_pct=range_pct,
        atr_pct=atr_pct,
        position_in_range=pos,
    )


def evaluate_entry(
    candles: list[Candle],
    config: VolatilityHunterConfig,
) -> VolatilitySignal | None:
    """تصمیم ورود."""
    if len(candles) < config.warmup_candles:
        return None

    current = candles[-1]
    price = float(current.close)
    rng = detect_range(candles, config)

    if not rng.is_valid:
        return None

    # ---------- بررسی منطقه‌ی خرید ----------
    buy_threshold = rng.low + (rng.high - rng.low) * (config.buy_zone_pct / 100)

    if price <= buy_threshold:
        sl = rng.low * (1 - config.stop_loss_pct / 100)
        tp = rng.mid + (rng.high - rng.mid) * 0.5  # نیمه‌ی بالایی

        confidence = min(95, 55 + int((1 - rng.position_in_range) * 40))

        return VolatilitySignal(
            should_trade=True,
            action="buy",
            entry_price=price,
            stop_loss=sl,
            take_profit=tp,
            reason=f"نزدیک کف range ({rng.position_in_range * 100:.0f}%) | range={rng.range_pct:.1f}%",
            confidence=confidence,
            range_info=rng,
        )

    return None


def evaluate_exit(
    candles: list[Candle],
    entry_price: float,
    stop_loss: float,
    take_profit: float,
    config: VolatilityHunterConfig,
) -> tuple[bool, float, str]:
    """تصمیم خروج."""
    if not candles:
        return False, 0, ""

    current = candles[-1]
    high = float(current.high)
    low = float(current.low)
    price = float(current.close)

    # SL
    if low <= stop_loss:
        return True, stop_loss, "stop_loss"

    # TP
    if high >= take_profit:
        return True, take_profit, "take_profit"

    # Breakout check
    rng = detect_range(candles, config)
    if rng.is_valid:
        # اگه از range خارج شد
        if price > rng.high * (1 + config.breakout_pct / 100):
            return True, price, "breakout_up"
        if price < rng.low * (1 - config.breakout_pct / 100):
            return True, price, "breakout_down"

    return False, 0, ""
