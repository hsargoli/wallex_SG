"""Anomaly Detector — تشخیص وضعیت غیرعادی بازار.

ایده: به جای پیش‌بینی، تشخیص می‌ده که "آیا الان شبیه گذشته‌ست یا نه؟"

استفاده:
  - اگه anomaly detected → سیگنال‌ها رو با احتیاط بگیر
  - اگه normal → سیگنال‌های معمولی

تکنیک: Isolation Forest (unsupervised)
"""

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

from app.domain.entities.candle import Candle


@dataclass(slots=True)
class AnomalyResult:
    is_anomaly: bool
    score: float  # -1 (anomaly) تا 1 (normal)
    severity: str  # normal / mild / severe
    reason: str
    features: dict[str, float]


def candles_to_features(candles: list[Candle]) -> pd.DataFrame:
    """ساخت feature ها برای anomaly detection."""
    df = pd.DataFrame(
        [
            {
                "time": c.time,
                "open": float(c.open),
                "high": float(c.high),
                "low": float(c.low),
                "close": float(c.close),
                "volume": float(c.volume),
            }
            for c in candles
        ]
    )

    out = pd.DataFrame(index=df.index)

    # بازده
    out["ret_1"] = df["close"].pct_change(1)
    out["ret_5"] = df["close"].pct_change(5)
    out["ret_20"] = df["close"].pct_change(20)

    # نوسان
    out["hl_pct"] = (df["high"] - df["low"]) / df["close"]
    out["volatility_10"] = out["ret_1"].rolling(10).std()
    out["volatility_30"] = out["ret_1"].rolling(30).std()

    # نسبت‌ها
    out["vol_ratio"] = df["volume"] / df["volume"].rolling(20).mean()
    out["vol_spike"] = df["volume"] / df["volume"].rolling(50).mean() - 1

    # موقعیت
    high20 = df["high"].rolling(20).max()
    low20 = df["low"].rolling(20).min()
    rng = (high20 - low20).replace(0, np.nan)
    out["pos_in_range"] = (df["close"] - low20) / rng

    # الگوی کندل
    body = (df["close"] - df["open"]).abs()
    out["body_ratio"] = body / (df["high"] - df["low"]).replace(0, np.nan)

    return out


def detect_anomaly(
    candles: list[Candle],
    contamination: float = 0.05,
) -> AnomalyResult:
    """
    تشخیص وضعیت غیرعادی.

    Args:
        candles: کندل‌ها
        contamination: درصد انتظار ناهنجاری (5% = معمول)

    Returns:
        AnomalyResult
    """
    if len(candles) < 100:
        return AnomalyResult(
            is_anomaly=False,
            score=0.0,
            severity="normal",
            reason="داده کافی نیست",
            features={},
        )

    # ساخت features
    X_full = candles_to_features(candles)
    last_row = X_full.iloc[[-1]]

    if last_row.isna().any(axis=1).iloc[0]:
        return AnomalyResult(
            is_anomaly=False,
            score=0.0,
            severity="normal",
            reason="feature ناقص",
            features={},
        )

    # آموزش Isolation Forest روی همه‌ی کندل‌های عادی
    X_train = X_full.dropna()
    if len(X_train) < 50:
        return AnomalyResult(
            is_anomaly=False,
            score=0.0,
            severity="normal",
            reason="داده کافی برای آموزش نیست",
            features={},
        )

    model = IsolationForest(
        contamination=contamination,
        random_state=42,
        n_estimators=100,
        max_samples=min(256, len(X_train)),
    )
    model.fit(X_train)

    # پیش‌بینی روی آخرین کندل
    pred = model.predict(last_row)[0]  # -1 یا 1
    score = float(model.score_samples(last_row)[0])  # -inf تا 0

    is_anomaly = pred == -1

    # شدت
    if is_anomaly:
        if score < -0.15:
            severity = "severe"
        else:
            severity = "mild"
    else:
        severity = "normal"

    # دلیل اصلی
    reasons = []
    features = last_row.iloc[0].to_dict()

    if abs(features.get("ret_1", 0)) > 0.02:
        reasons.append(f"بازده کندل اخیر {features['ret_1'] * 100:.2f}%")
    if features.get("vol_ratio", 0) > 3:
        reasons.append(f"حجم {features['vol_ratio']:.1f}× میانگین")
    if features.get("hl_pct", 0) > 0.03:
        reasons.append(f"نوسان {features['hl_pct'] * 100:.2f}%")
    if features.get("vol_spike", 0) > 2:
        reasons.append(f"جهش حجم {features['vol_spike']:.1f}×")

    reason = " | ".join(reasons) if reasons else "وضعیت غیرمعمول"

    return AnomalyResult(
        is_anomaly=is_anomaly,
        score=round(score, 4),
        severity=severity,
        reason=reason,
        features={k: round(v, 4) for k, v in features.items()},
    )
