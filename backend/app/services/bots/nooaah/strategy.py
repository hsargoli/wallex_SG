"""Nooaah strategy — منطق خالص انتخاب و پیشنهاد معامله.

هیچ I/O، هیچ exchange call. فقط تصمیم روی داده‌ی آماده.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from app.domain.analysis.entities.regime import RegimeType
from app.domain.entities.candle import Candle
from app.infrastructure.analysis.rule_based_classifier import RuleBasedClassifier
from app.services.bots.nooaah.config import NooaahConfig


@dataclass(frozen=True, slots=True)
class TradeProposal:
    """پیشنهاد معامله برای یه نماد."""

    symbol: str
    action: str  # "BUY" | "WAIT"
    entry: float
    take_profit: float
    stop_loss: float
    confidence: int
    regime: str
    reason: str


def propose_trade(
    symbol: str,
    candles: Sequence[Candle],
    config: NooaahConfig,
) -> TradeProposal | None:
    """پیشنهاد معامله — یا None اگه شرایط ورود نیست.

    شرایط ورود:
      - regime == TRENDING_UP
      - is_tradeable == True
      - confidence >= config.min_confidence
    """
    if len(candles) < config.min_candles:
        return None

    classifier = RuleBasedClassifier()
    ctx = candles[-config.context_candles :]
    result = classifier.classify(ctx)

    if result.regime != RegimeType.TRENDING_UP:
        return None
    if not result.is_tradeable:
        return None
    if result.confidence < config.min_confidence:
        return None

    entry = float(candles[-1].close)
    if entry <= 0:
        return None

    atr_pct = (result.atr_pct / 100) if result.atr_pct else 0.01
    tp = entry * (1 + config.tp_atr_mult * atr_pct)
    sl = entry * (1 - config.sl_atr_mult * atr_pct)

    return TradeProposal(
        symbol=symbol,
        action="BUY",
        entry=entry,
        take_profit=tp,
        stop_loss=sl,
        confidence=result.confidence,
        regime=result.regime.value,
        reason=" | ".join(result.reasons),
    )


def pick_best(
    proposals: Sequence[TradeProposal | None],
) -> TradeProposal | None:
    """از بین پیشنهادها، بهترین (بالاترین confidence) رو انتخاب کن."""
    valid = [p for p in proposals if p is not None]
    if not valid:
        return None
    return max(valid, key=lambda p: p.confidence)


def decide(
    symbols_candles: dict[str, Sequence[Candle]],
    config: NooaahConfig,
) -> TradeProposal | None:
    """تصمیم نهایی: از دیکشنری نماد→کندل، بهترین پیشنهاد رو بده."""
    proposals = [
        propose_trade(sym, candles, config)
        for sym, candles in symbols_candles.items()
    ]
    return pick_best(proposals)
