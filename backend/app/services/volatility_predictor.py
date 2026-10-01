"""Volatility Predictor — پیش‌بینی نوسان آینده.

ایده: نوسان قابل پیش‌بینی‌تر از جهته (Volatility Clustering).

استفاده:
  - SL/TP بر اساس نوسان پیش‌بینی‌شده
  - Position Sizing بر اساس نوسان
"""

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor

from app.domain.entities.candle import Candle


@dataclass(slots=True)
class VolatilityResult:
    predicted_vol_pct: float  # درصد نوسان پیش‌بینی‌شده
    current_vol_pct: float  # نوسان فعلی
    regime: str  # low / normal / high / extreme
    recommended_sl_pct: float  # حد ضرر پیشنهادی
    recommended_tp_pct: float  # حد سود پیشنهادی
    recommended_size_pct: float  # اندازه پوزیشن (0-100)
    reason: str


def build_vol_features(candles: list[Candle]) -> pd.DataFrame:
    """Features برای پیش‌بینی نوسان."""
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

    # Historical volatility در بازه‌های مختلف
    ret = df["close"].pct_change()
    out["vol_5"] = ret.rolling(5).std()
    out["vol_10"] = ret.rolling(10).std()
    out["vol_20"] = ret.rolling(20).std()
    out["vol_50"] = ret.rolling(50).std()

    # نسبت‌ها (نوسان کوتاه به بلند)
    out["vol_ratio_5_20"] = out["vol_5"] / out["vol_20"].replace(0, np.nan)
    out["vol_ratio_10_50"] = out["vol_10"] / out["vol_50"].replace(0, np.nan)

    # ATR%
    hl = df["high"] - df["low"]
    out["atr_pct"] = hl / df["close"]
    out["atr_ma_5"] = out["atr_pct"].rolling(5).mean()
    out["atr_ma_20"] = out["atr_pct"].rolling(20).mean()

    # حجم
    out["vol_vol_ratio"] = df["volume"] / df["volume"].rolling(20).mean()

    # بازده
    out["ret_abs_5"] = ret.abs().rolling(5).mean()
    out["ret_abs_20"] = ret.abs().rolling(20).mean()

    return out


def build_vol_target(candles: list[Candle], lookahead: int = 24) -> pd.Series:
    """Target: ATR% در N کندل آینده."""
    df = pd.DataFrame(
        [{"high": float(c.high), "low": float(c.low), "close": float(c.close)} for c in candles]
    )
    hl = (df["high"] - df["low"]) / df["close"]
    # میانگین نوسان N کندل آینده
    future_vol = hl.shift(-1).rolling(lookahead).mean().shift(-(lookahead - 1))
    return future_vol * 100  # درصد


def classify_volatility(predicted_vol_pct: float) -> str:
    """دسته‌بندی نوسان."""
    if predicted_vol_pct < 0.5:
        return "low"
    elif predicted_vol_pct < 1.5:
        return "normal"
    elif predicted_vol_pct < 3.0:
        return "high"
    else:
        return "extreme"


def predict_volatility(candles: list[Candle]) -> VolatilityResult | None:
    """پیش‌بینی نوسان آینده."""
    if len(candles) < 150:
        return None

    X_full = build_vol_features(candles)
    y_full = build_vol_target(candles)

    mask = ~(X_full.isna().any(axis=1) | y_full.isna())
    X = X_full[mask]
    y = y_full[mask]

    if len(X) < 50:
        return None

    # آموزش روی همه‌ی داده‌ی موجود (به‌جز آخرین بخش برای اعتبارسنجی)
    split = int(len(X) * 0.8)
    X_train = X.iloc[:split]
    y_train = y.iloc[:split]

    model = GradientBoostingRegressor(
        n_estimators=80,
        max_depth=3,
        learning_rate=0.05,
        min_samples_leaf=20,
        subsample=0.8,
        random_state=42,
    )
    model.fit(X_train, y_train)

    # پیش‌بینی برای آخرین کندل
    last_features = X_full.iloc[[-1]]
    if last_features.isna().any(axis=1).iloc[0]:
        return None

    predicted = float(model.predict(last_features)[0])
    predicted = max(0.1, min(10.0, predicted))  # cap

    # نوسان فعلی
    current_atr_pct = (
        float(X_full["atr_pct"].iloc[-1] * 100) if not pd.isna(X_full["atr_pct"].iloc[-1]) else 1.0
    )

    regime = classify_volatility(predicted)

    # توصیه‌ها
    if regime == "low":
        sl_pct = 1.0
        tp_pct = 2.0
        size_pct = 80
    elif regime == "normal":
        sl_pct = 1.5
        tp_pct = 3.0
        size_pct = 50
    elif regime == "high":
        sl_pct = 2.5
        tp_pct = 5.0
        size_pct = 30
    else:  # extreme
        sl_pct = 4.0
        tp_pct = 8.0
        size_pct = 15

    return VolatilityResult(
        predicted_vol_pct=round(predicted, 3),
        current_vol_pct=round(current_atr_pct, 3),
        regime=regime,
        recommended_sl_pct=sl_pct,
        recommended_tp_pct=tp_pct,
        recommended_size_pct=size_pct,
        reason=f"نوسان پیش‌بینی: {predicted:.2f}% → {regime}",
    )
