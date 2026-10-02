"""اسکریپت v3: 4h + معیارهای درست + class_weight.

تغییرات:
- تایم‌فریم 4h (بیشتر داده: ~16 ماه از Wallex)
- معیارها: Precision, Recall, F1, AUC
- class_weight='balanced' برای مقابله با عدم تعادل
- Precision@top-K (برای تصمیم‌گیری معاملاتی)
"""

import asyncio

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import TimeSeriesSplit

from app.application.use_cases.get_candles import GetCandlesUseCase
from app.core.config import get_settings
from app.infrastructure.exchange.wallex.client import WallexExchange

SYMBOL = "BTCTMN"
TIMEFRAME = "4h"
N_CANDLES = 1000
RANDOM_STATE = 42


async def fetch_candles() -> pd.DataFrame:
    settings = get_settings()
    ex = WallexExchange.create(settings)
    try:
        uc = GetCandlesUseCase(exchange=ex)
        candles = await uc.execute(
            symbol=SYMBOL, timeframe=TIMEFRAME, limit=N_CANDLES
        )
    finally:
        await ex.aclose()

    return pd.DataFrame(
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


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame(index=df.index)

    # بازده
    out["return_1"] = df["close"].pct_change(1)
    out["return_3"] = df["close"].pct_change(3)
    out["return_5"] = df["close"].pct_change(5)
    out["return_1_lag1"] = out["return_1"].shift(1)

    # MA / EMA
    ma20 = df["close"].rolling(20).mean()
    ma50 = df["close"].rolling(50).mean()
    out["ma_20_ratio"] = df["close"] / ma20 - 1.0
    out["ma_50_ratio"] = df["close"] / ma50 - 1.0

    ema9 = df["close"].ewm(span=9, adjust=False).mean()
    ema21 = df["close"].ewm(span=21, adjust=False).mean()
    out["ema_9_21_diff"] = (ema9 - ema21) / df["close"]

    # موقعیت قیمت
    high20 = df["high"].rolling(20).max()
    low20 = df["low"].rolling(20).min()
    range20 = (high20 - low20).replace(0, np.nan)
    out["price_position_20"] = (df["close"] - low20) / range20

    # حجم
    vol_ma20 = df["volume"].rolling(20).mean()
    out["volume_ratio"] = df["volume"] / vol_ma20.replace(0, np.nan)
    out["volume_trend"] = (
        df["volume"].rolling(5).mean() / df["volume"].rolling(20).mean()
    ) - 1.0

    # شکل کندل
    hl_range = df["high"] - df["low"]
    body = (df["close"] - df["open"]).abs()
    out["hl_range"] = hl_range / df["close"]
    out["body_ratio"] = body / hl_range.replace(0, np.nan)
    out["upper_wick_ratio"] = (
        df["high"] - df[["open", "close"]].max(axis=1)
    ) / hl_range.replace(0, np.nan)
    out["lower_wick_ratio"] = (
        df[["open", "close"]].min(axis=1) - df["low"]
    ) / hl_range.replace(0, np.nan)
    out["candle_direction"] = (df["close"] > df["open"]).astype(int)

    # RSI
    delta = df["close"].diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()
    rs = gain / loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    out["rsi_14"] = rsi
    out["rsi_lag1"] = rsi.shift(1)
    out["rsi_change"] = rsi - rsi.shift(1)

    # نوسان
    out["volatility_5"] = df["close"].pct_change().rolling(5).std()
    out["volatility_20"] = df["close"].pct_change().rolling(20).std()

    # زمان
    dt = pd.to_datetime(df["time"], unit="s", utc=True)
    out["hour_of_day"] = dt.dt.hour
    out["day_of_week"] = dt.dt.dayofweek

    return out


def build_label(df: pd.DataFrame, n: int) -> pd.Series:
    return (df["close"].shift(-n) > df["close"]).astype(int)


def precision_at_top_k(y_true: np.ndarray, y_prob: np.ndarray, k_pct: float) -> float:
    """از k_pct بهترین پیش‌بینی (احتمال بالا)، چند درصد درست بود؟"""
    k = max(1, int(len(y_prob) * k_pct))
    top_idx = np.argsort(y_prob)[-k:]
    return float(y_true[top_idx].mean())


def evaluate(X: pd.DataFrame, y: pd.Series, name: str) -> None:
    mask = ~(X.isna().any(axis=1) | y.isna())
    X_clean = X[mask].reset_index(drop=True)
    y_clean = y[mask].reset_index(drop=True)

    if len(X_clean) < 100 or y_clean.nunique() < 2:
        print(f"⚠️  {name}: data insufficient")
        return

    tscv = TimeSeriesSplit(n_splits=5)

    metrics = {"acc": [], "prec": [], "rec": [], "f1": [], "auc": [], "p_top20": []}
    all_y = []
    all_prob = []

    for train_idx, test_idx in tscv.split(X_clean):
        X_tr = X_clean.iloc[train_idx]
        X_te = X_clean.iloc[test_idx]
        y_tr = y_clean.iloc[train_idx]
        y_te = y_clean.iloc[test_idx]

        if y_tr.nunique() < 2:
            continue

        model = RandomForestClassifier(
            n_estimators=200,
            max_depth=12,
            min_samples_leaf=10,
            class_weight="balanced",   # ← کلید تغییر
            random_state=RANDOM_STATE,
            n_jobs=-1,
        )
        model.fit(X_tr, y_tr)

        y_pred = model.predict(X_te)
        y_prob = model.predict_proba(X_te)[:, 1]

        metrics["acc"].append(accuracy_score(y_te, y_pred))
        metrics["prec"].append(precision_score(y_te, y_pred, zero_division=0))
        metrics["rec"].append(recall_score(y_te, y_pred, zero_division=0))
        metrics["f1"].append(f1_score(y_te, y_pred, zero_division=0))
        try:
            metrics["auc"].append(roc_auc_score(y_te, y_prob))
        except ValueError:
            pass
        metrics["p_top20"].append(precision_at_top_k(y_te.values, y_prob, 0.2))

        all_y.extend(y_te.tolist())
        all_prob.extend(y_prob.tolist())

    if not metrics["acc"]:
        return

    baseline = float(y_clean.mean())

    print(f"\n{'='*70}")
    print(f"📊 {name}  (n={len(X_clean)}, baseline={baseline:.3f})")
    print(f"{'='*70}")
    print(f"  Accuracy:           {np.mean(metrics['acc']):.4f}")
    print(f"  Precision (UP):     {np.mean(metrics['prec']):.4f}")
    print(f"  Recall (UP):        {np.mean(metrics['rec']):.4f}")
    print(f"  F1:                 {np.mean(metrics['f1']):.4f}")
    if metrics["auc"]:
        print(f"  AUC-ROC:            {np.mean(metrics['auc']):.4f}   ← معیار اصلی")
    print(f"  Precision@Top20%:   {np.mean(metrics['p_top20']):.4f}   ← برای معامله")


async def main() -> None:
    print(f"📥 دریافت {N_CANDLES} کندل {TIMEFRAME} برای {SYMBOL}...")
    df = await fetch_candles()
    print(f"✅ {len(df)} کندل")

    if len(df) < 100:
        print("❌ داده کافی نیست")
        return

    print(f"   از {pd.to_datetime(df['time'].iloc[0], unit='s')}")
    print(f"   تا {pd.to_datetime(df['time'].iloc[-1], unit='s')}")

    print("\n🔧 ساخت Features...")
    X = build_features(df)
    print(f"✅ {X.shape[1]} feature")

    print("\n🚀 ارزیابی Target های مختلف:")

    for n in [1, 2, 3, 4, 6]:
        y = build_label(df, n)
        evaluate(X, y, f"direction_{n} ({TIMEFRAME})")


if __name__ == "__main__":
    asyncio.run(main())
