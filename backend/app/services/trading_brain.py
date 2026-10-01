"""Trading Brain — تصمیم‌گیرنده‌ی نهایی ربات.

ترکیب:
  - Rules: سیگنال اصلی
  - Anomaly: محافظت
  - Volatility: تنظیم SL/TP/Size
"""

from dataclasses import dataclass

from app.domain.entities.candle import Candle
from app.services.anomaly_detector import detect_anomaly
from app.services.bottom_detector import detect_bottom
from app.services.volatility_predictor import predict_volatility


@dataclass(slots=True)
class TradingDecision:
    should_trade: bool
    action: str  # buy / sell / hold
    confidence: int  # 0-100
    position_size_pct: float  # 0-100 (چند درصد سرمایه)
    stop_loss_pct: float
    take_profit_pct: float
    reason: str
    details: dict


def make_decision(
    candles: list[Candle],
    base_capital_pct: float = 100.0,
) -> TradingDecision:
    """
    تصمیم نهایی برای ورود به معامله.

    Args:
        candles: کندل‌ها
        base_capital_pct: درصد پایه سرمایه برای هر پوزیشن

    Returns:
        TradingDecision
    """
    details = {}

    # ---------- ۱. سیگنال قوانین ----------
    rule = detect_bottom(candles)
    details["rule_score"] = rule.score
    details["rule_strength"] = rule.strength
    details["rule_is_bottom"] = rule.is_bottom

    # قوانین باید کف قوی تشخیص بدن (score >= 6)
    if rule.score < 6:
        return TradingDecision(
            should_trade=False,
            action="hold",
            confidence=0,
            position_size_pct=0,
            stop_loss_pct=0,
            take_profit_pct=0,
            reason=f"سیگنال کف ضعیف (score={rule.score} < 6)",
            details=details,
        )

    # ---------- ۲. Anomaly Check ----------
    anomaly = detect_anomaly(candles)
    details["anomaly_severity"] = anomaly.severity
    details["anomaly_score"] = anomaly.score

    size_multiplier = 1.0
    if anomaly.severity == "severe":
        return TradingDecision(
            should_trade=False,
            action="hold",
            confidence=0,
            position_size_pct=0,
            stop_loss_pct=0,
            take_profit_pct=0,
            reason=f"وضعیت غیرعادی شدید: {anomaly.reason}",
            details=details,
        )
    elif anomaly.severity == "mild":
        size_multiplier = 0.5
        details["anomaly_note"] = "پوزیشن نصف به‌خاطر anomaly خفیف"

    # ---------- ۳. Volatility Sizing ----------
    vol = predict_volatility(candles)
    if vol:
        details["vol_predicted"] = vol.predicted_vol_pct
        details["vol_regime"] = vol.regime
        details["vol_recommended_sl"] = vol.recommended_sl_pct
        details["vol_recommended_tp"] = vol.recommended_tp_pct
        details["vol_recommended_size"] = vol.recommended_size_pct

        base_size = vol.recommended_size_pct
        sl_pct = vol.recommended_sl_pct
        tp_pct = vol.recommended_tp_pct
    else:
        # پیش‌فرض اگه Volatility Predictor کار نکرد
        base_size = 50.0
        sl_pct = 1.5
        tp_pct = 3.0
        details["vol_fallback"] = True

    # ---------- ۴. تصمیم نهایی ----------
    final_size_pct = (base_size / 100.0) * base_capital_pct * size_multiplier

    # اطمینان بر اساس rule score
    confidence = min(95, 40 + rule.score * 8)

    # کاهش اطمینان اگه anomaly خفیف باشه
    if anomaly.severity == "mild":
        confidence = int(confidence * 0.7)

    reasons = []
    reasons.append(f"کف (score={rule.score})")
    if anomaly.severity == "mild":
        reasons.append("anomaly خفیف")
    if vol:
        reasons.append(f"vol={vol.regime}")

    return TradingDecision(
        should_trade=True,
        action="buy",
        confidence=confidence,
        position_size_pct=round(final_size_pct, 1),
        stop_loss_pct=sl_pct,
        take_profit_pct=tp_pct,
        reason=" | ".join(reasons),
        details=details,
    )
