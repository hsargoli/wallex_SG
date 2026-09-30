"""Signal Engine v2 — تولید سیگنال خرید/فروش با ۶ قانون.

قوانین:
  1. RSI (Oversold/Overbought)
  2. EMA Cross (9/21)
  3. Volume Confirmation
  4. MACD (cross + histogram)
  5. Bollinger Bands (breakout)
  6. ATR (position sizing helper)
"""

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum

from app.domain.entities.candle import Candle
from app.services.indicators import (
    atr,
    bollinger,
    ema,
    macd,
    rsi,
    volume_sma,
)


class SignalType(StrEnum):
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"


class SignalStrength(StrEnum):
    WEAK = "weak"
    MEDIUM = "medium"
    STRONG = "strong"


@dataclass(slots=True)
class Rule:
    name: str
    passed: bool
    score: int  # -3..+3 (منفی برای SELL، مثبت برای BUY)
    reason: str


@dataclass(slots=True)
class Signal:
    type: SignalType
    strength: SignalStrength
    confidence: int
    reasons: list[str]
    rules: list[Rule]
    current_price: Decimal
    indicators: dict[str, Decimal | None]
    # اهداف
    stop_loss: Decimal | None = None
    take_profit: Decimal | None = None
    risk_reward: Decimal | None = None
    # متادیتا
    buy_score: int = 0
    sell_score: int = 0


def _last(values: list) -> Decimal | None:
    for v in reversed(values):
        if v is not None:
            return v
    return None


def generate_signal(candles: list[Candle]) -> Signal:
    """تولید سیگنال v2 با ۶ قانون."""
    if len(candles) < 50:
        return Signal(
            type=SignalType.HOLD,
            strength=SignalStrength.WEAK,
            confidence=0,
            reasons=["داده کافی نیست (حداقل ۵۰ کندل لازم است)"],
            rules=[],
            current_price=candles[-1].close if candles else Decimal(0),
            indicators={},
        )

    # ---------- محاسبه‌ی اندیکاتورها ----------
    ema9 = ema(candles, 9)
    ema21 = ema(candles, 21)
    rsi14 = rsi(candles, 14)
    vol_ma = volume_sma(candles, 20)
    macd_line, macd_signal, macd_hist = macd(candles)
    bb_upper, bb_middle, bb_lower = bollinger(candles, 20)
    atr14 = atr(candles, 14)

    last_close = candles[-1].close
    last_volume = candles[-1].volume

    current_ema9 = _last(ema9)
    current_ema21 = _last(ema21)
    current_rsi = _last(rsi14)
    current_vol_ma = _last(vol_ma)
    current_macd = _last(macd_line)
    current_signal = _last(macd_signal)
    current_hist = _last(macd_hist)
    current_bb_upper = _last(bb_upper)
    current_bb_middle = _last(bb_middle)
    current_bb_lower = _last(bb_lower)
    current_atr = _last(atr14)

    prev_hist = macd_hist[-2] if len(macd_hist) >= 2 else None
    prev_ema9 = ema9[-2] if len(ema9) >= 2 else None
    prev_ema21 = ema21[-2] if len(ema21) >= 2 else None

    indicators = {
        "ema_9": current_ema9,
        "ema_21": current_ema21,
        "rsi_14": current_rsi,
        "volume": last_volume,
        "volume_ma_20": current_vol_ma,
        "macd": current_macd,
        "macd_signal": current_signal,
        "macd_hist": current_hist,
        "bb_upper": current_bb_upper,
        "bb_middle": current_bb_middle,
        "bb_lower": current_bb_lower,
        "atr_14": current_atr,
    }

    rules: list[Rule] = []

    # ---------- قانون ۱: RSI ----------
    if current_rsi is not None:
        if current_rsi < Decimal(30):
            rules.append(Rule("RSI Oversold", True, 2, f"RSI = {current_rsi:.1f} (بیش‌فروش)"))
        elif current_rsi < Decimal(40):
            rules.append(
                Rule("RSI Near Oversold", True, 1, f"RSI = {current_rsi:.1f} (نزدیک بیش‌فروش)")
            )
        elif current_rsi > Decimal(70):
            rules.append(Rule("RSI Overbought", True, -2, f"RSI = {current_rsi:.1f} (بیش‌خرید)"))
        elif current_rsi > Decimal(60):
            rules.append(
                Rule("RSI Near Overbought", True, -1, f"RSI = {current_rsi:.1f} (نزدیک بیش‌خرید)")
            )
        else:
            rules.append(Rule("RSI Neutral", False, 0, f"RSI = {current_rsi:.1f} (خنثی)"))

    # ---------- قانون ۲: EMA Cross ----------
    if all(x is not None for x in [current_ema9, current_ema21, prev_ema9, prev_ema21]):
        if prev_ema9 <= prev_ema21 and current_ema9 > current_ema21:
            rules.append(
                Rule("Golden Cross", True, 3, "Golden Cross: EMA(9) از پایین EMA(21) قطع شد")
            )
        elif prev_ema9 >= prev_ema21 and current_ema9 < current_ema21:
            rules.append(
                Rule("Death Cross", True, -3, "Death Cross: EMA(9) از بالا EMA(21) قطع شد")
            )
        elif current_ema9 > current_ema21:
            rules.append(Rule("Uptrend", True, 1, "روند صعودی: EMA(9) > EMA(21)"))
        elif current_ema9 < current_ema21:
            rules.append(Rule("Downtrend", True, -1, "روند نزولی: EMA(9) < EMA(21)"))

    # ---------- قانون ۳: Volume ----------
    if current_vol_ma is not None and current_vol_ma > 0:
        vol_ratio = last_volume / current_vol_ma
        if vol_ratio > Decimal("1.5"):
            # جهت رو از سایر قوانین می‌گیریم
            partial_buy = sum(r.score for r in rules if r.score > 0)
            partial_sell = sum(-r.score for r in rules if r.score < 0)
            if partial_buy > partial_sell:
                rules.append(
                    Rule(
                        "Volume Confirm BUY", True, 2, f"حجم {vol_ratio:.1f}× میانگین (تأیید خرید)"
                    )
                )
            elif partial_sell > partial_buy:
                rules.append(
                    Rule(
                        "Volume Confirm SELL",
                        True,
                        -2,
                        f"حجم {vol_ratio:.1f}× میانگین (تأیید فروش)",
                    )
                )
            else:
                rules.append(Rule("Volume High", True, 0, f"حجم {vol_ratio:.1f}× میانگین"))
        elif vol_ratio < Decimal("0.5"):
            rules.append(Rule("Volume Low", False, 0, f"حجم {vol_ratio:.1f}× میانگین (کم)"))

    # ---------- قانون ۴: MACD ----------
    if current_macd is not None and current_signal is not None:
        if current_macd > current_signal and current_hist and current_hist > 0:
            rules.append(Rule("MACD Bullish", True, 2, "MACD > Signal (صعودی)"))
        elif current_macd < current_signal and current_hist and current_hist < 0:
            rules.append(Rule("MACD Bearish", True, -2, "MACD < Signal (نزولی)"))
        # هیستوگرام در حال تغییر جهت
        if prev_hist is not None and current_hist is not None:
            if prev_hist < 0 and current_hist > 0:
                rules.append(Rule("MACD Histogram Flip", True, 1, "هیستوگرام MACD مثبت شد"))
            elif prev_hist > 0 and current_hist < 0:
                rules.append(Rule("MACD Histogram Flip Down", True, -1, "هیستوگرام MACD منفی شد"))

    # ---------- قانون ۵: Bollinger Bands ----------
    if all(x is not None for x in [current_bb_upper, current_bb_lower, current_bb_middle]):
        if last_close <= current_bb_lower:
            rules.append(
                Rule("BB Lower Break", True, 2, "قیمت زیر Bollinger پایین (احتمال بازگشت)")
            )
        elif last_close >= current_bb_upper:
            rules.append(
                Rule("BB Upper Break", True, -2, "قیمت بالای Bollinger بالا (احتمال اصلاح)")
            )
        elif last_close > current_bb_middle:
            rules.append(Rule("BB Upper Half", True, 1, "قیمت در نیمه‌ی بالایی باند"))
        elif last_close < current_bb_middle:
            rules.append(Rule("BB Lower Half", True, -1, "قیمت در نیمه‌ی پایینی باند"))

    # ---------- جمع‌بندی ----------
    buy_score = sum(r.score for r in rules if r.score > 0)
    sell_score = sum(-r.score for r in rules if r.score < 0)

    if buy_score == 0 and sell_score == 0:
        return Signal(
            type=SignalType.HOLD,
            strength=SignalStrength.WEAK,
            confidence=0,
            reasons=["هیچ قانونی فعال نیست"],
            rules=rules,
            current_price=last_close,
            indicators=indicators,
            buy_score=0,
            sell_score=0,
        )

    if buy_score == sell_score:
        return Signal(
            type=SignalType.HOLD,
            strength=SignalStrength.WEAK,
            confidence=0,
            reasons=["سیگنال متضاد — توصیه‌ی صبر"],
            rules=rules,
            current_price=last_close,
            indicators=indicators,
            buy_score=buy_score,
            sell_score=sell_score,
        )

    if buy_score > sell_score:
        sig_type = SignalType.BUY
        passed_rules = [r for r in rules if r.score > 0 and r.passed]
        max_score = buy_score
    else:
        sig_type = SignalType.SELL
        passed_rules = [r for r in rules if r.score < 0 and r.passed]
        max_score = sell_score

    # قدرت
    if max_score >= 6:
        strength = SignalStrength.STRONG
        confidence = min(95, 60 + max_score * 4)
    elif max_score >= 3:
        strength = SignalStrength.MEDIUM
        confidence = min(80, 45 + max_score * 5)
    else:
        strength = SignalStrength.WEAK
        confidence = min(60, 35 + max_score * 5)

    # ---------- Stop Loss / Take Profit (بر اساس ATR) ----------
    stop_loss = None
    take_profit = None
    risk_reward = None
    if current_atr is not None and current_atr > 0:
        if sig_type == SignalType.BUY:
            stop_loss = last_close - (current_atr * Decimal(2))
            take_profit = last_close + (current_atr * Decimal(4))
        else:
            stop_loss = last_close + (current_atr * Decimal(2))
            take_profit = last_close - (current_atr * Decimal(4))

        if stop_loss and take_profit:
            risk = abs(last_close - stop_loss)
            reward = abs(take_profit - last_close)
            if risk > 0:
                risk_reward = reward / risk

    return Signal(
        type=sig_type,
        strength=strength,
        confidence=confidence,
        reasons=[r.reason for r in passed_rules],
        rules=rules,
        current_price=last_close,
        indicators=indicators,
        stop_loss=stop_loss,
        take_profit=take_profit,
        risk_reward=risk_reward,
        buy_score=buy_score,
        sell_score=sell_score,
    )
