"""مدل ساده‌تر با Regularization قوی.

استراتژی:
  1. فقط 7 feature مهم (از 22)
  2. Regularization شدید (depth=4, leaf=50)
  3. Train/Test split بر اساس زمان واقعی
  4. Early stopping
"""

import asyncio
from datetime import datetime, timezone

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, roc_auc_score

from app.application.use_cases.get_candles import GetCandlesUseCase
from app.core.config import get_settings
from app.infrastructure.exchange.wallex.client import WallexExchange
from app.services.ml_bottom_model import build_features, candles_to_df


SYMBOLS = ["BTCTMN", "ETHTMN", "XRPTMN", "DOGETMN", "SOLTMN"]
TF = "15m"
N_CANDLES = 1000

# فقط 7 feature برتر از تحلیل قبلی
TOP_FEATURES = [
    "ma50_dist",
    "ma_cross",
    "vol_ma_ratio",
    "rsi_low_5",
    "rsi",
    "pos_in_range",
    "atr_pct",
]

# پارامترهای مدل ساده
LOOKAHEAD = 24
TP_PCT = 2.0
SL_PCT = 1.5


async def fetch_all():
    settings = get_settings()
    async def one(sym):
        ex = WallexExchange.create(settings)
        try:
            uc = GetCandlesUseCase(exchange=ex)
            return sym, await uc.execute(symbol=sym, timeframe=TF, limit=N_CANDLES)
        except Exception:
            return sym, []
        finally:
            await ex.aclose()
    results = await asyncio.gather(*[one(s) for s in SYMBOLS])
    return {s: c for s, c in results if c}


def build_label(df, lookahead=24, tp_pct=2.0, sl_pct=1.5):
    labels = []
    for i in range(len(df)):
        if i + lookahead >= len(df):
            labels.append(np.nan)
            continue
        entry = df["close"].iloc[i]
        tp = entry * (1 + tp_pct / 100)
        sl = entry * (1 - sl_pct / 100)
        future = df.iloc[i + 1: i + lookahead + 1]
        hit_tp = hit_sl = None
        for j, (_, row) in enumerate(future.iterrows()):
            if hit_sl is None and row["low"] <= sl:
                hit_sl = j
            if hit_tp is None and row["high"] >= tp:
                hit_tp = j
            if hit_tp is not None or hit_sl is not None:
                break
        if hit_tp is not None and (hit_sl is None or hit_tp < hit_sl):
            labels.append(1)
        elif hit_sl is not None:
            labels.append(0)
        else:
            labels.append(np.nan)
    return pd.Series(labels, index=df.index)


def split_by_time(df, split_pct=0.6):
    """تقسیم بر اساس زمان واقعی (نه تصادفی)."""
    n = len(df)
    split_idx = int(n * split_pct)
    return df.iloc[:split_idx], df.iloc[split_idx:]


async def main():
    print(f"📥 دریافت {len(SYMBOLS)} نماد...\n")
    markets_data = await fetch_all()
    print(f"✅ {len(markets_data)} نماد\n")

    all_train_X, all_train_y = [], []
    all_test_X, all_test_y = [], []

    for symbol, candles in markets_data.items():
        df = candles_to_df(candles)
        if len(df) < 200:
            continue

        X_full = build_features(df)
        y_full = build_label(df)

        # فقط featureهای مهم
        X_full = X_full[TOP_FEATURES]

        # تقسیم زمانی — 60% اول train، 40% آخر test
        X_train, X_test = split_by_time(X_full, 0.6)
        y_train, y_test = split_by_time(y_full, 0.6)

        all_train_X.append(X_train)
        all_train_y.append(y_train)
        all_test_X.append(X_test)
        all_test_y.append(y_test)

        print(f"  {symbol:10}  train={len(X_train):>4}  test={len(X_test):>4}")

    X_train = pd.concat(all_train_X, ignore_index=True)
    y_train = pd.concat(all_train_y, ignore_index=True)
    X_test = pd.concat(all_test_X, ignore_index=True)
    y_test = pd.concat(all_test_y, ignore_index=True)

    # پاکسازی
    mask_tr = ~(X_train.isna().any(axis=1) | y_train.isna())
    X_train = X_train[mask_tr].reset_index(drop=True)
    y_train = y_train[mask_tr].reset_index(drop=True)

    mask_te = ~(X_test.isna().any(axis=1) | y_test.isna())
    X_test = X_test[mask_te].reset_index(drop=True)
    y_test = y_test[mask_te].reset_index(drop=True)

    print(f"\n📊 Train: {len(X_train)}  |  Test: {len(X_test)}")
    print(f"   Train positive rate: {y_train.mean()*100:.1f}%")
    print(f"   Test  positive rate: {y_test.mean()*100:.1f}%\n")

    # ---------- مدل ساده ----------
    print("🎓 آموزش مدل ساده (regularized)...")
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=4,           # ← کم‌عمق‌تر
        min_samples_leaf=50,   # ← برگ‌های بزرگ‌تر
        min_samples_split=100,
        max_features=3,        # ← کمتر
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X_train, y_train)

    # ---------- ارزیابی ----------
    print(f"\n{'='*70}")
    print("📊 نتایج:")
    print(f"{'='*70}")

    for name, X_eval, y_eval in [
        ("TRAIN", X_train, y_train),
        ("TEST ", X_test, y_test),
    ]:
        if len(X_eval) == 0:
            continue
        pred = model.predict(X_eval)
        prob = model.predict_proba(X_eval)[:, 1]
        print(f"\n  {name}:  n={len(X_eval)}")
        print(f"    Accuracy:   {accuracy_score(y_eval, pred):.4f}")
        print(f"    Precision:  {precision_score(y_eval, pred, zero_division=0):.4f}")
        print(f"    Recall:     {recall_score(y_eval, pred, zero_division=0):.4f}")
        try:
            auc = roc_auc_score(y_eval, prob)
            print(f"    AUC-ROC:    {auc:.4f}")
        except ValueError:
            pass

    # Feature importance
    imp = pd.Series(model.feature_importances_, index=TOP_FEATURES).sort_values(ascending=False)
    print("\n🔍 Feature Importance:")
    for n, v in imp.items():
        bar = "█" * int(v * 50)
        print(f"  {n:20} {v:.4f}  {bar}")


if __name__ == "__main__":
    asyncio.run(main())
