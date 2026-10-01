"""Bounce Scalper v3 — Trailing Stop + فیلتر قوی‌تر.

نوآوری:
  - Trailing Stop هوشمند (ریسک صفر بعد از 1×ATR سود)
  - فیلتر ورود قوی‌تر (افت + کندل + ATR)
"""

from dataclasses import dataclass

from app.domain.entities.candle import Candle
from app.services.indicators import atr, ema, rsi

# ---------- تنظیمات ----------
DROP_THRESHOLD_PCT = 1.5  # افت بیشتر (از 1.0)
LOOKBACK_HIGH = 20
TIMEOUT_CANDLES = 24  # 6 ساعت (بیشتر برای فرصت)

# Trailing Stop levels
SL_ATR_MULT = 1.5  # SL اولیه
TRAIL_1_ATR = 1.0  # وقتی 1×ATR سود → SL = entry (breakeven)
TRAIL_2_ATR = 2.0  # وقتی 2×ATR سود → SL = entry + 1×ATR
TRAIL_3_ATR = 3.0  # وقتی 3×ATR سود → SL = entry + 2×ATR

MIN_SL_PCT = 0.6
MAX_SL_PCT = 2.5

MIN_RSI = 20
MAX_RSI = 48

# فیلتر قوی‌تر
MIN_BODY_RATIO = 0.25  # کندل فعلی باید بدنه داشته باشه
MIN_DROP = 1.5  # افت حداقل


@dataclass(slots=True)
class BounceDecision:
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


def make_bounce_decision(candles: list[Candle]) -> BounceDecision:
    """تصمیم ورود با فیلتر قوی‌تر."""
    if len(candles) < 30:
        return BounceDecision(
            should_trade=False,
            action="hold",
            entry_price=0,
            take_profit=0,
            stop_loss=0,
            reason="داده کم",
            drop_pct=0,
            rsi=0,
            atr_pct=0,
        )

    current = candles[-1]
    entry_price = float(current.close)

    # ---------- ۱. افت ----------
    lookback = candles[-LOOKBACK_HIGH:]
    recent_high = max(float(c.high) for c in lookback)
    drop_pct = (recent_high - entry_price) / recent_high * 100

    if drop_pct < DROP_THRESHOLD_PCT:
        return BounceDecision(
            should_trade=False,
            action="hold",
            entry_price=entry_price,
            take_profit=0,
            stop_loss=0,
            reason=f"افت کم ({drop_pct:.2f}%)",
            drop_pct=round(drop_pct, 2),
            rsi=0,
            atr_pct=0,
        )

    # ---------- ۲. RSI ----------
    rsi14_vals = rsi(candles, 14)
    current_rsi = _last(rsi14_vals)
    rsi_float = float(current_rsi) if current_rsi else 50

    if rsi_float > MAX_RSI or rsi_float < MIN_RSI:
        return BounceDecision(
            should_trade=False,
            action="hold",
            entry_price=entry_price,
            take_profit=0,
            stop_loss=0,
            reason=f"RSI نامناسب ({rsi_float:.0f})",
            drop_pct=round(drop_pct, 2),
            rsi=round(rsi_float, 1),
            atr_pct=0,
        )

    # ---------- ۳. کیفیت کندل (فیلتر جدید) ----------
    hl_range = float(current.high) - float(current.low)
    if hl_range <= 0:
        return BounceDecision(
            should_trade=False,
            action="hold",
            entry_price=entry_price,
            take_profit=0,
            stop_loss=0,
            reason="کندل بی‌حرکت",
            drop_pct=round(drop_pct, 2),
            rsi=round(rsi_float, 1),
            atr_pct=0,
        )

    body = abs(float(current.close) - float(current.open))
    body_ratio = body / hl_range
    lower_wick = min(float(current.open), float(current.close)) - float(current.low)
    lower_wick_ratio = lower_wick / hl_range
    is_green = float(current.close) > float(current.open)

    # شرط جدید: کندل سبز قوی OR سایه‌ی پایین واضح
    has_good_candle = (is_green and body_ratio >= MIN_BODY_RATIO) or (lower_wick_ratio >= 0.45)

    if not has_good_candle:
        return BounceDecision(
            should_trade=False,
            action="hold",
            entry_price=entry_price,
            take_profit=0,
            stop_loss=0,
            reason="کندل ضعیف",
            drop_pct=round(drop_pct, 2),
            rsi=round(rsi_float, 1),
            atr_pct=0,
        )

    # ---------- ۴. ATR ----------
    atr14_vals = atr(candles, 14)
    current_atr = _last(atr14_vals)
    if current_atr is None:
        return BounceDecision(
            should_trade=False,
            action="hold",
            entry_price=entry_price,
            take_profit=0,
            stop_loss=0,
            reason="ATR نامشخص",
            drop_pct=round(drop_pct, 2),
            rsi=round(rsi_float, 1),
            atr_pct=0,
        )

    atr_pct = float(current_atr) / entry_price * 100

    sl_pct = SL_ATR_MULT * atr_pct
    sl_pct = max(MIN_SL_PCT, min(MAX_SL_PCT, sl_pct))

    # TP خیلی بزرگ (عملاً بی‌نهایت — Trailing Stop کار می‌کنه)
    tp_pct = 15.0  # TP خیلی دور
    tp = entry_price * (1 + tp_pct / 100)
    sl = entry_price * (1 - sl_pct / 100)

    # فیلتر سقوط آزاد
    ema20_vals = ema(candles, 20)
    ema20 = _last(ema20_vals)
    if ema20:
        dist = (float(ema20) - entry_price) / float(ema20) * 100
        if dist > 4:
            return BounceDecision(
                should_trade=False,
                action="hold",
                entry_price=entry_price,
                take_profit=0,
                stop_loss=0,
                reason=f"سقوط آزاد ({dist:.1f}%)",
                drop_pct=round(drop_pct, 2),
                rsi=round(rsi_float, 1),
                atr_pct=round(atr_pct, 2),
            )

    return BounceDecision(
        should_trade=True,
        action="buy",
        entry_price=entry_price,
        take_profit=tp,
        stop_loss=sl,
        reason=f"افت {drop_pct:.1f}% | RSI={rsi_float:.0f} | ATR={atr_pct:.2f}%",
        drop_pct=round(drop_pct, 2),
        rsi=round(rsi_float, 1),
        atr_pct=round(atr_pct, 2),
    )


def check_bounce_exit_trailing(
    entry_price: float,
    tp_price: float,
    sl_price: float,
    atr_value: float,
    current_sl: float,
    candle: Candle,
    candles_in_position: int,
) -> tuple[bool, float, str, float]:
    """
    بررسی خروج با Trailing Stop.

    Returns: (should_exit, exit_price, reason, new_sl)
    """
    # چک SL فعلی
    if candle.low <= current_sl:
        reason = "stop_loss" if current_sl < entry_price else "trailing_sl"
        return True, current_sl, reason, current_sl

    # چک TP (خیلی دور، عملاً هرگز)
    if candle.high >= tp_price:
        return True, tp_price, "take_profit", current_sl

    # Trailing Stop logic
    new_sl = current_sl
    profit_atr = (float(candle.high) - entry_price) / atr_value if atr_value > 0 else 0

    # وقتی 1×ATR سود → SL = entry (breakeven)
    if profit_atr >= TRAIL_1_ATR:
        candidate_sl = entry_price
        if candidate_sl > new_sl:
            new_sl = candidate_sl

    # وقتی 2×ATR سود → SL = entry + 1×ATR
    if profit_atr >= TRAIL_2_ATR:
        candidate_sl = entry_price + TRAIL_1_ATR * atr_value
        if candidate_sl > new_sl:
            new_sl = candidate_sl

    # وقتی 3×ATR سود → SL = entry + 2×ATR
    if profit_atr >= TRAIL_3_ATR:
        candidate_sl = entry_price + TRAIL_2_ATR * atr_value
        if candidate_sl > new_sl:
            new_sl = candidate_sl

    # Timeout
    if candles_in_position >= TIMEOUT_CANDLES:
        return True, float(candle.close), "timeout", new_sl

    return False, 0, "", new_sl


def check_bounce_exit(
    entry_price: float,
    tp_price: float,
    sl_price: float,
    candle: Candle,
    candles_in_position: int,
) -> tuple[bool, float, str]:
    """نسخه ساده برای سازگاری با تست قبلی."""
    if candle.low <= sl_price:
        return True, sl_price, "stop_loss"
    if candle.high >= tp_price:
        return True, tp_price, "take_profit"
    if candles_in_position >= TIMEOUT_CANDLES:
        return True, float(candle.close), "timeout"
    return False, 0, ""
