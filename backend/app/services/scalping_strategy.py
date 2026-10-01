"""Scalping Strategy — خرید در افت، فروش در سود کوچک."""

from dataclasses import dataclass
from decimal import Decimal

from app.domain.entities.candle import Candle
from app.services.signal_engine import SignalType, generate_signal

TAKE_PROFIT_PCT = Decimal("2.0")
STOP_LOSS_PCT = Decimal("1.5")
TIMEOUT_CANDLES = 4
MIN_CONFIDENCE = 45


@dataclass(slots=True)
class EntrySignal:
    symbol: str
    price: Decimal
    take_profit: Decimal
    stop_loss: Decimal
    confidence: int
    reason: str


@dataclass(slots=True)
class Position:
    symbol: str
    entry_price: Decimal
    quantity: Decimal
    take_profit: Decimal
    stop_loss: Decimal
    entry_time: int
    entry_candle_idx: int


def evaluate_entry(candles: list[Candle], symbol: str) -> EntrySignal | None:
    if len(candles) < 100:
        return None
    signal = generate_signal(candles)
    if signal.type != SignalType.BUY:
        return None
    if signal.confidence < MIN_CONFIDENCE:
        return None
    price = candles[-1].close
    tp = price * (Decimal(1) + TAKE_PROFIT_PCT / Decimal(100))
    sl = price * (Decimal(1) - STOP_LOSS_PCT / Decimal(100))
    risk = price - sl
    reward = tp - price
    if risk <= 0:
        return None
    rr = reward / risk
    if rr < Decimal("1.3"):
        return None
    return EntrySignal(
        symbol=symbol,
        price=price,
        take_profit=tp,
        stop_loss=sl,
        confidence=signal.confidence,
        reason=f"BUY conf={signal.confidence}%",
    )


def check_exit(position: Position, candle: Candle, current_idx: int) -> tuple[bool, str]:
    if candle.high >= position.take_profit:
        return True, "take_profit"
    if candle.low <= position.stop_loss:
        return True, "stop_loss"
    if (current_idx - position.entry_candle_idx) >= TIMEOUT_CANDLES:
        return True, "timeout"
    return False, ""
