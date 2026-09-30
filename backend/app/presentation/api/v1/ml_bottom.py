"""ML Bottom Detection endpoint — ترکیب ML + قوانین."""

from fastapi import APIRouter, HTTPException, status

from app.application.use_cases.get_candles import GetCandlesUseCase
from app.presentation.api.deps import ExchangeDep
from app.services.bottom_detector import detect_bottom
from app.services.ml_bottom_model import load_model, predict_probability

router = APIRouter(prefix="/ml/bottom", tags=["ML Bottom"])

# مدل رو یک‌بار لود می‌کنیم
_model = None


def get_model():
    global _model
    if _model is None:
        try:
            _model = load_model()
        except FileNotFoundError:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="مدل ML آموزش ندیده. لطفاً train کن.",
            ) from None
    return _model


@router.get("/predict/{symbol}")
async def predict(
    symbol: str,
    exchange: ExchangeDep,
    tf: str = "15m",
    limit: int = 500,
):
    """تشخیص کف با ML + قوانین."""
    try:
        use_case = GetCandlesUseCase(exchange=exchange)
        candles = await use_case.execute(symbol=symbol, timeframe=tf, limit=limit)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    if not candles or len(candles) < 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="داده کافی نیست",
        )

    # ۱. ML
    model = get_model()
    ml_prob = predict_probability(model, candles)

    # ۲. قوانین
    rule = detect_bottom(candles)

    # ۳. ترکیب
    # - ML به تنهایی: prob >= 0.65
    # - قوانین به تنهایی: is_bottom=True
    # - ترکیبی: prob >= 0.55 AND score >= 4
    ml_ok = ml_prob is not None and ml_prob >= 0.45
    rule_ok = rule.is_bottom
    combined_ok = ml_prob is not None and ml_prob >= 0.45 and rule.score >= 4

    # تصمیم نهایی
    if ml_ok and rule_ok:
        verdict = "strong_buy"
        confidence = int((ml_prob or 0) * 100)
        reason = "ML + قوانین هر دو تایید کردن"
    elif combined_ok:
        verdict = "buy"
        confidence = int((ml_prob or 0) * 100)
        reason = "ترکیب ML + قوانین"
    elif ml_ok:
        verdict = "weak_buy"
        confidence = int((ml_prob or 0) * 100)
        reason = "فقط ML تایید کرد"
    elif rule_ok:
        verdict = "weak_buy"
        confidence = rule.score * 10
        reason = "فقط قوانین تایید کردن"
    else:
        verdict = "wait"
        confidence = 0
        reason = "هنوز کف نیست"

    return {
        "symbol": symbol,
        "timeframe": tf,
        "current_price": str(candles[-1].close),
        "verdict": verdict,
        "confidence": confidence,
        "reason": reason,
        "ml": {
            "probability": round(ml_prob, 4) if ml_prob is not None else None,
            "threshold_strong": 0.55,
            "threshold_weak": 0.45,
            "passed": ml_ok,
        },
        "rules": {
            "is_bottom": rule.is_bottom,
            "score": rule.score,
            "strength": rule.strength,
            "reasons": rule.reasons,
        },
    }
