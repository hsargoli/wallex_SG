"""ML برای تشخیص کف — نسخه اول روی BTC."""

import asyncio
import time
from decimal import Decimal

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import TimeSeriesSplit

from app.application.use_cases.get_candles import GetCandlesUseCase
from app.core.config import get_settings
from app.infrastructure.exchange.wallex.client import WallexExchange

# ---------- تنظیمات ----------
SYMBOL = "BTCTMN"
TIMEFRAME = "1h"
N_CANDLES = 800
LOOKAHEAD = 24          # بررسی 24 کندل بعد
TARGET_GAIN = 1.5       # هدف سود
TARGET_LOSS = 1.0       # حد ضرر
RANDOM_STATE = 42


async def fetch_candles() -> pd.DataFrame:
    settings = get_settings()
    ex = WallexExchange.create(settings)
    try:
        uc = GetCandlesUseCase(exchange=ex)
        candles = await uc.execute(symbol=SYMBOL, timeframe=TIMEFRAME, limit=N_CANDLES)
    finally:
        await ex.aclose()

    df = pd.DataFrame([
        {"time": c.time, "open": float(c.open), "high": float(c.high),
         "low": float(c.low), "close": float(c.close), "volume": float(c.volume)}
        for c in candles
    ])
    return df


def rsi_series(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = (-delta.clip(upper=0)).rolling(period).mean()
    rs = gain / loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """ساخت ویژگی‌ها."""
    out = pd.DataFrame(index=df.index)

    # RSI
    out["rsi"] = rsi_series(df["close"], 14)
    out["rsi_lag1"] = out["rsi"].shift(1)
    out["rsi_lag3"] = out["rsi"].shift(3)
    out["rsi_change"] = out["rsi"] - out["rsi"].shift(1)

    # بازده
    out["ret_1"] = df["close"].pct_change(1)
    out["ret_3"] = df["close"].pct_change(3)
    out["ret_5"] = df["close"].pct_change(5)

    # MA
    ma20 = df["close"].rolling(20).mean()
    ma50 = df["close"].rolling(50).mean()
    out["ma20_dist"] = (df["close"] - ma20) / ma20
    out["ma50_dist"] = (df["close"] - ma50) / ma50
    out["ma_cross"] = (ma20 - ma50) / ma50

    # موقعیت قیمت
    high20 = df["high"].rolling(20).max()
    low20 = df["low"].rolling(20).min()
    rng = (high20 - low20).replace(0, np.nan)
    out["pos_in_range"] = (df["close"] - low20) / rng
    out["near_low"] = (df["low"] - low20) / rng

    # حجم
    vol_ma = df["volume"].rolling(20).mean()
    out["vol_ratio"] = df["volume"] / vol_ma.replace(0, np.nan)
    out["vol_ma_ratio"] = vol_ma / df["volume"].rolling(50).mean()

    # شکل کندل
    hl = df["high"] - df["low"]
    out["body_ratio"] = (df["close"] - df["open"]).abs() / hl.replace(0, np.nan)
    out["upper_wick"] = (df["high"] - df[["open", "close"]].max(axis=1)) / hl.replace(0, np.nan)
    out["lower_wick"] = (df[["open", "close"]].min(axis=1) - df["low"]) / hl.replace(0, np.nan)
    out["is_red"] = (df["close"] < df["open"]).astype(int)

    # کندل‌های قرمز متوالی
    red = (df["close"] < df["open"]).astype(int)
    out["consec_red"] = red.groupby((red != red.shift()).cumsum()).cumsum()

    # نوسان
    out["atr_pct"] = (hl / df["close"])

    # RSI divergence ساده (کف قیمت پایین‌تر، RSI بالاتر)
    out["price_low_5"] = df["low"].rolling(5).min() / df["low"]
    out["rsi_low_5"] = out["rsi"].rolling(5).min()

    return out


def build_label(df: pd.DataFrame) -> pd.Series:
    """
    Label: آیا در N کندل بعد، ابتدا به TP رسیده یا SL؟
    1 = ابتدا TP (کف درست)
    0 = ابتدا SL یا هیچکدام
    """
    labels = []
    for i in range(len(df)):
        if i + LOOKAHEAD >= len(df):
            labels.append(np.nan)
            continue

        entry = df["close"].iloc[i]
        tp = entry * (1 + TARGET_GAIN / 100)
        sl = entry * (1 - TARGET_LOSS / 100)

        future = df.iloc[i + 1 : i + LOOKAHEAD + 1]

        # اولین برخورد
        hit_tp_idx = None
        hit_sl_idx = None
        for j, (_, row) in enumerate(future.iterrows()):
            if hit_sl_idx is None and row["low"] <= sl:
                hit_sl_idx = j
            if hit_tp_idx is None and row["high"] >= tp:
                hit_tp_idx = j
            if hit_tp_idx is not None or hit_sl_idx is not None:
                break

        if hit_tp_idx is not None and (hit_sl_idx is None or hit_tp_idx < hit_sl_idx):
            labels.append(1)
        elif hit_sl_idx is not None:
            labels.append(0)
        else:
            labels.append(np.nan)

    return pd.Series(labels, index=df.index)


def evaluate(X, y, name):
    mask = ~(X.isna().any(axis=1) | y.isna())
    X_clean = X[mask].reset_index(drop=True)
    y_clean = y[mask].reset_index(drop=True)

    if len(X_clean) < 100 or y_clean.nunique() < 2:
        print(f"⚠️ {name}: داده کافی نیست ({len(X_clean)})")
        return

    tscv = TimeSeriesSplit(n_splits=5)
    all_y, all_pred, all_prob = [], [], []

    for train_idx, test_idx in tscv.split(X_clean):
        X_tr, X_te = X_clean.iloc[train_idx], X_clean.iloc[test_idx]
        y_tr, y_te = y_clean.iloc[train_idx], y_clean.iloc[test_idx]

        if y_tr.nunique() < 2:
            continue

        model = RandomForestClassifier(
            n_estimators=200, max_depth=8, min_samples_leaf=10,
            class_weight="balanced", random_state=RANDOM_STATE, n_jobs=-1,
        )
        model.fit(X_tr, y_tr)
        pred = model.predict(X_te)
        prob = model.predict_proba(X_te)[:, 1]

        all_y.extend(y_te.tolist())
        all_pred.extend(pred.tolist())
        all_prob.extend(prob.tolist())

    if not all_y:
        return

    print(f"\n{'='*60}")
    print(f"📊 {name}  (n={len(X_clean)}, positives={y_clean.sum()})")
    print(f"{'='*60}")
    print(f"  Accuracy:   {accuracy_score(all_y, all_pred):.4f}")
    print(f"  Precision:  {precision_score(all_y, all_pred, zero_division=0):.4f}")
    print(f"  Recall:     {recall_score(all_y, all_pred, zero_division=0):.4f}")
    try:
        print(f"  AUC-ROC:    {roc_auc_score(all_y, all_prob):.4f}")
    except ValueError:
        pass

    # Feature importance
    mask = ~(X.isna().any(axis=1) | y.isna())
    X_clean = X[mask].reset_index(drop=True)
    y_clean = y[mask].reset_index(drop=True)
    final = RandomForestClassifier(
        n_estimators=200, max_depth=8, min_samples_leaf=10,
        class_weight="balanced", random_state=RANDOM_STATE, n_jobs=-1,
    )
    final.fit(X_clean, y_clean)
    imp = pd.Series(final.feature_importances_, index=X_clean.columns).sort_values(ascending=False)
    print("\n🔍 Top 10 features:")
    for name, v in imp.head(10).items():
        print(f"  {name:20} {v:.4f}")


async def main():
    print(f"📥 دریافت {N_CANDLES} کندل {TIMEFRAME} برای {SYMBOL}...")
    df = await fetch_candles()
    print(f"✅ {len(df)} کندل\n")

    print("🔧 ساخت Features...")
    X = build_features(df)
    print(f"✅ {X.shape[1]} feature\n")

    print("🏷️ ساخت Labels...")
    y = build_label(df)
    print(f"✅ توزیع: {y.value_counts().to_dict()}")
    print(f"   نرخ کف‌های موفق: {y.mean()*100:.1f}%\n")

    print("🚀 آموزش RandomForest...")
    evaluate(X, y, f"{SYMBOL} {TIMEFRAME}")


if __name__ == "__main__":
    asyncio.run(main())
