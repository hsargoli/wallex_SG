"""اسکریپت آموزش سریع ML روی داده کندل والکس.

هدف: بررسی اینکه آیا RandomForest روی داده‌ی واقعی BTC می‌تونه
جهت ۴ کندل بعدی رو با دقت بالاتر از شانس پیش‌بینی کنه.
"""

import asyncio
import sys
import time
from decimal import Decimal

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import TimeSeriesSplit

from app.application.use_cases.get_candles import GetCandlesUseCase
from app.core.config import get_settings
from app.infrastructure.exchange.wallex.client import WallexExchange

# ---------- تنظیمات ----------
SYMBOL = "BTCTMN"
TIMEFRAME = "1h"
N_CANDLES = 1000       # پارامتری — بعداً می‌تونیم زیاد کنیم
LOOKAHEAD = 4          # چند کندل بعد
RANDOM_STATE = 42


# ---------- ۱. دریافت داده ----------
async def fetch_candles() -> pd.DataFrame:
    """دریافت کندل‌ها از والکس و تبدیل به DataFrame."""
    settings = get_settings()
    ex = WallexExchange.create(settings)
    try:
        uc = GetCandlesUseCase(exchange=ex)
        candles = await uc.execute(
            symbol=SYMBOL, timeframe=TIMEFRAME, limit=N_CANDLES
        )
    finally:
        await ex.aclose()

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
    return df


# ---------- ۲. ساخت Features ----------
def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """ساخت ویژگی‌های عددی از کندل‌ها."""
    out = pd.DataFrame(index=df.index)

    # --- بازده ---
    out["return_1"] = df["close"].pct_change(1)
    out["return_3"] = df["close"].pct_change(3)
    out["return_5"] = df["close"].pct_change(5)

    # --- میانگین‌های متحرک ---
    ma20 = df["close"].rolling(20).mean()
    ma50 = df["close"].rolling(50).mean()
    out["ma_20_ratio"] = df["close"] / ma20 - 1.0
    out["ma_50_ratio"] = df["close"] / ma50 - 1.0

    # --- EMA ---
    ema9 = df["close"].ewm(span=9, adjust=False).mean()
    ema21 = df["close"].ewm(span=21, adjust=False).mean()
    out["ema_9_21_diff"] = (ema9 - ema21) / df["close"]

    # --- حجم ---
    vol_ma20 = df["volume"].rolling(20).mean()
    out["volume_ratio"] = df["volume"] / vol_ma20

    # --- شکل کندل ---
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

    # --- RSI (14) ---
    delta = df["close"].diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()
    rs = gain / loss.replace(0, np.nan)
    out["rsi_14"] = 100 - (100 / (1 + rs))

    # --- زمان ---
    dt = pd.to_datetime(df["time"], unit="s", utc=True)
    out["hour_of_day"] = dt.dt.hour
    out["day_of_week"] = dt.dt.dayofweek

    return out


# ---------- ۳. ساخت Labels ----------
def build_labels(df: pd.DataFrame) -> pd.Series:
    """Label: آیا قیمت ۴ کندل بعد از این کندل بالاتره؟ (1=بله)"""
    future_close = df["close"].shift(-LOOKAHEAD)
    return (future_close > df["close"]).astype(int)


# ---------- ۴. آموزش و ارزیابی ----------
def train_and_evaluate(X: pd.DataFrame, y: pd.Series) -> None:
    """آموزش RandomForest با TimeSeriesSplit و گزارش دقت."""
    # حذف ردیف‌های NaN
    mask = ~(X.isna().any(axis=1) | y.isna())
    X_clean = X[mask].reset_index(drop=True)
    y_clean = y[mask].reset_index(drop=True)

    print(f"\n📊 داده‌ی تمیز: {len(X_clean)} نمونه × {X_clean.shape[1]} feature")
    print(f"📊 توزیع label: {y_clean.value_counts().to_dict()}")

    # TimeSeriesSplit (چون داده زمانی‌ه)
    tscv = TimeSeriesSplit(n_splits=5)
    fold_accuracies: list[float] = []
    all_y_true: list[int] = []
    all_y_pred: list[int] = []

    for fold, (train_idx, test_idx) in enumerate(tscv.split(X_clean), 1):
        X_train = X_clean.iloc[train_idx]
        X_test = X_clean.iloc[test_idx]
        y_train = y_clean.iloc[train_idx]
        y_test = y_clean.iloc[test_idx]

        model = RandomForestClassifier(
            n_estimators=100,
            max_depth=8,
            min_samples_leaf=20,
            random_state=RANDOM_STATE,
            n_jobs=-1,
        )
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)

        acc = accuracy_score(y_test, y_pred)
        fold_accuracies.append(acc)
        all_y_true.extend(y_test.tolist())
        all_y_pred.extend(y_pred.tolist())
        print(f"  Fold {fold}: train={len(train_idx):5}  test={len(test_idx):5}  acc={acc:.4f}")

    mean_acc = float(np.mean(fold_accuracies))
    std_acc = float(np.std(fold_accuracies))

    print(f"\n🎯 دقت میانگین: {mean_acc:.4f} ± {std_acc:.4f}")
    print(f"🎯 Baseline (همیشه up): {y_clean.mean():.4f}")
    print(f"🎯 بهبود بر baseline: {(mean_acc - y_clean.mean())*100:+.2f}%")

    print("\n📋 گزارش کامل:")
    print(classification_report(all_y_true, all_y_pred, digits=3))

    # Feature Importance روی کل داده
    final_model = RandomForestClassifier(
        n_estimators=100,
        max_depth=8,
        min_samples_leaf=20,
        random_state=RANDOM_STATE,
        n_jobs=-1,
    )
    final_model.fit(X_clean, y_clean)
    importances = pd.Series(
        final_model.feature_importances_, index=X_clean.columns
    ).sort_values(ascending=False)

    print("\n🔍 Top 10 Feature Importance:")
    for name, imp in importances.head(10).items():
        print(f"  {name:25} {imp:.4f}")


# ---------- main ----------
async def main() -> None:
    print(f"📥 دریافت {N_CANDLES} کندل {TIMEFRAME} برای {SYMBOL}...")
    df = await fetch_candles()
    print(f"✅ {len(df)} کندل دریافت شد")

    print("\n🔧 ساخت Features...")
    X = build_features(df)
    print(f"✅ {X.shape[1]} feature ساخته شد: {list(X.columns)}")

    print("\n🏷️  ساخت Labels...")
    y = build_labels(df)
    print(f"✅ توزیع: {y.value_counts().to_dict()}")

    print("\n🚀 آموزش RandomForest...")
    train_and_evaluate(X, y)


if __name__ == "__main__":
    asyncio.run(main())
