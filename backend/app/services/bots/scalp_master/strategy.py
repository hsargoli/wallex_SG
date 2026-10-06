"""استراتژی Scalp Master — اسکالپ نزولی v2.

منطق:
  ۱. تشخیص سقوط (افت از سقف N کندل اخیر)
  ۲. تشخیص توقف سقوط (۲ کندل سبز پشت سر هم)
  ۳. RSI در محدوده اشباع فروش
  ۴. SL پویا (ATR-based) + TP = 3×ATR
"""

from dataclasses import dataclass

from app.domain.entities.candle import Candle
from app.services.bots.scalp_master.config import ScalpMasterConfig
from app.services.indicators import atr, ema, rsi


@dataclass(slots=True)
class ScalpSignal:
    """سیگنال ورود."""

    should_trade: bool
    action: str
    entry_price: float
    take_profit: float
    stop_loss: float
    reason: str
    drop_pct: float
    rsi: float
    atr_pct: float


def _last(values):
    for v in reversed(values):
        if v is not None:
            return v
    return None


def evaluate_entry(
    candles: list[Candle],
    config: ScalpMasterConfig,
) -> ScalpSignal | None:
    """تصمیم ورود با تأیید برگشت."""
    if len(candles) < config.warmup_candles:
        return None

    current = candles[-1]
    entry_price = float(current.close)

    # ---------- ۱. افت ----------
    lookback = candles[-config.lookback_high:]
    recent_high = max(float(c.high) for c in lookback)
    drop_pct = (recent_high - entry_price) / recent_high * 100

    if drop_pct < config.drop_threshold_pct:
        return None

    # ---------- ۲. تأیید برگشت: ۲ کندل سبز ----------
    if len(candles) < 3:
        return None

    prev = candles[-2]
    curr = candles[-1]

    prev_is_green = float(prev.close) > float(prev.open)
    curr_is_green = float(curr.close) > float(curr.open)
    curr_higher = float(curr.close) > float(prev.close)

    if not (prev_is_green and curr_is_green and curr_higher):
        return None

    # ---------- ۳. RSI ----------
    rsi_vals = rsi(candles, config.rsi_period)
    current_rsi = _last(rsi_vals)
    rsi_float = float(current_rsi) if current_rsi else 50.0

    if rsi_float < config.rsi_min or rsi_float > config.rsi_max:
        return None

    # ---------- ۴. کیفیت کندل ----------
    hl_range = float(curr.high) - float(curr.low)
    if hl_range <= 0:
        return None

    body = abs(float(curr.close) - float(curr.open))
    body_ratio = body / hl_range

    if body_ratio < config.min_body_ratio:
        return None

    # ---------- ۵. ATR ----------
    atr_vals = atr(candles, 14)
    atr_val = _last(atr_vals)
    if atr_val is None or atr_val <= 0:
        return None

    atr_float = float(atr_val)
    atr_pct = atr_float / entry_price * 100

    # ---------- ۶. فیلتر سقوط آزاد ----------
    ema20_vals = ema(candles, 20)
    ema20 = _last(ema20_vals)
    if ema20:
        dist = (float(ema20) - entry_price) / float(ema20) * 100
        if dist > config.max_dist_from_ema:
            return None

    # ---------- ۷. SL/TP پویا ----------
    sl = entry_price - config.sl_atr_mult * atr_float
    tp = entry_price + config.tp_atr_mult * atr_float

    # محافظت: SL حداقل
    min_sl_pct = config.min_sl_pct
    max_sl_price = entry_price * (1 - min_sl_pct / 100)
    if sl > max_sl_price:
        sl = max_sl_price

    return ScalpSignal(
        should_trade=True,
        action="buy",
        entry_price=entry_price,
        take_profit=tp,
        stop_loss=sl,
        reason=f"افت {drop_pct:.1f}% | ۲ کندل سبز | RSI={rsi_float:.0f} | ATR={atr_pct:.2f}%",
        drop_pct=round(drop_pct, 2),
        rsi=round(rsi_float, 1),
        atr_pct=round(atr_pct, 2),
    )


def evaluate_exit(
    candles: list[Candle],
    entry_price: float,
    stop_loss: float,
    take_profit: float,
    candles_in_position: int,
    config: ScalpMasterConfig,
) -> tuple[bool, float, str]:
    """تصمیم خروج."""
    if not candles:
        return False, 0, ""

    current = candles[-1]
    high = float(current.high)
    low = float(current.low)
    close = float(current.close)

    # SL
    if low <= stop_loss:
        return True, stop_loss, "stop_loss"

    # TP
    if high >= take_profit:
        return True, take_profit, "take_profit"

    # Timeout
    if candles_in_position >= config.timeout_candles:
        return True, close, "timeout"

    return False, 0, ""
