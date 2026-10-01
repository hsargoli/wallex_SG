"""Simple Bot — ربات قانونی خالص.

استراتژی:
  1. کف‌شناسی قانونی (Bottom Detector, score >= 6)
  2. SL = 1.5% / TP = 2.0%
  3. Position Size = 50% سرمایه
  4. Max 2 پوزیشن همزمان
"""

from dataclasses import dataclass

from app.domain.entities.candle import Candle
from app.services.bottom_detector import detect_bottom

# ---------- تنظیمات ----------
MIN_SCORE = 6  # حداقل امتیاز کف‌شناسی
TAKE_PROFIT_PCT = 2.0  # هدف سود
STOP_LOSS_PCT = 1.5  # حد ضرر
TIMEOUT_CANDLES = 12  # حداکثر ۳ ساعت (بهینه‌شده)
POSITION_SIZE_PCT = 50.0  # 50% سرمایه
MAX_POSITIONS = 2
FEE_PCT = 0.2


@dataclass(slots=True)
class SimpleDecision:
    should_trade: bool
    action: str  # buy / hold
    entry_price: float
    take_profit: float
    stop_loss: float
    position_pct: float
    confidence: int
    reason: str


def make_simple_decision(candles: list[Candle]) -> SimpleDecision:
    """تصمیم ربات ساده."""
    if len(candles) < 100:
        return SimpleDecision(
            should_trade=False,
            action="hold",
            entry_price=0,
            take_profit=0,
            stop_loss=0,
            position_pct=0,
            confidence=0,
            reason="داده کافی نیست",
        )

    # ---------- فیلتر روند (CRITICAL) ----------
    from app.services.indicators import ema
    ema20_vals = ema(candles, 20)
    ema50_vals = ema(candles, 50)
    ema20 = next((v for v in reversed(ema20_vals) if v is not None), None)
    ema50 = next((v for v in reversed(ema50_vals) if v is not None), None)

    entry_price = float(candles[-1].close)

    if ema20 is not None and ema50 is not None and ema20 < ema50:
        # روند نزولی → معامله نکن
        return SimpleDecision(
            should_trade=False, action="hold",
            entry_price=entry_price, take_profit=0, stop_loss=0,
            position_pct=0, confidence=0,
            reason="روند نزولی (EMA20 < EMA50)",
        )

    rule = detect_bottom(candles)

    # شرط ورود: score >= 6
    if rule.score < MIN_SCORE:
        return SimpleDecision(
            should_trade=False,
            action="hold",
            entry_price=entry_price,
            take_profit=0,
            stop_loss=0,
            position_pct=0,
            confidence=0,
            reason=f"کف ضعیف (score={rule.score} < {MIN_SCORE})",
        )

    tp = entry_price * (1 + TAKE_PROFIT_PCT / 100)
    sl = entry_price * (1 - STOP_LOSS_PCT / 100)

    # اطمینان بر اساس score
    confidence = min(95, 50 + rule.score * 6)

    return SimpleDecision(
        should_trade=True,
        action="buy",
        entry_price=entry_price,
        take_profit=tp,
        stop_loss=sl,
        position_pct=POSITION_SIZE_PCT,
        confidence=confidence,
        reason=f"کف قوی (score={rule.score}, {rule.strength})",
    )


def check_simple_exit(
    entry_price: float,
    tp_price: float,
    sl_price: float,
    candle: Candle,
    candles_in_position: int,
) -> tuple[bool, float, str]:
    """
    بررسی خروج.
    Returns: (should_exit, exit_price, reason)
    """
    # TP
    if candle.high >= tp_price:
        return True, tp_price, "take_profit"

    # SL
    if candle.low <= sl_price:
        return True, sl_price, "stop_loss"

    # Timeout
    if candles_in_position >= TIMEOUT_CANDLES:
        return True, float(candle.close), "timeout"

    return False, 0, ""
