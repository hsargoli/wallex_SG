"""Replay روی کل سپتامبر با قابلیت تست چند مدل.

ایده: هر بار یه مدل جدید، نتیجه رو مقایسه کن.
"""

import asyncio
from datetime import datetime

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, roc_auc_score
from sklearn.svm import SVC
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import KNeighborsClassifier
from sklearn.gaussian_process import GaussianProcessClassifier
from sklearn.gaussian_process.kernels import RBF, ConstantKernel

from app.application.use_cases.get_candles import GetCandlesUseCase
from app.core.config import get_settings
from app.infrastructure.exchange.wallex.client import WallexExchange
from app.services.ml_bottom_model import build_features, candles_to_df


SYMBOLS = ["BTCTMN", "ETHTMN", "XRPTMN", "DOGETMN", "SOLTMN"]
TF = "15m"
N_CANDLES = 2000
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
        except Exception as e:
            print(f"  ❌ {sym}: {e}")
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


def get_models():
    """همه‌ی مدل‌های قابل تست."""
    return {
        # Baseline
        "RF (baseline)": RandomForestClassifier(
            n_estimators=200, max_depth=6, min_samples_leaf=30,
            random_state=42, n_jobs=-1,
        ),
        # ساده و مقاوم
        "Logistic Regression": LogisticRegression(
            max_iter=1000, C=0.1, random_state=42,
        ),
        # SVM — برای داده کم عالی
        "SVM (RBF)": SVC(
            kernel="rbf", C=1.0, gamma="scale",
            probability=True, random_state=42,
        ),
        # k-NN
        "k-NN (k=10)": KNeighborsClassifier(
            n_neighbors=10, weights="distance", n_jobs=-1,
        ),
        # Gaussian Process — برای داده کم ایده‌آل
        "Gaussian Process": GaussianProcessClassifier(
            kernel=ConstantKernel(1.0) * RBF(1.0),
            n_restarts_optimizer=0,
            random_state=42,
        ),
    }


async def main():
    print(f"📥 دریافت {len(SYMBOLS)} نماد × {TF}...\n")
    markets_data = await fetch_all()

    train_X_parts, train_y_parts = [], []
    test_X_parts, test_y_parts = [], []

    for symbol, candles in markets_data.items():
        df = candles_to_df(candles)
        if len(df) < 200:
            continue
        # تاریخ شروع و پایان
        first_time = datetime.fromtimestamp(candles[0].time).strftime("%m-%d")
        last_time = datetime.fromtimestamp(candles[-1].time).strftime("%m-%d")

        X = build_features(df)
        y = build_label(df)
        n = len(X)
        split = int(n * 0.6)
        train_X_parts.append(X.iloc[:split])
        train_y_parts.append(y.iloc[:split])
        test_X_parts.append(X.iloc[split:])
        test_y_parts.append(y.iloc[split:])
        print(f"  {symbol:10}  {first_time}→{last_time}  train={split:>5}  test={n-split:>5}")

    X_train = pd.concat(train_X_parts, ignore_index=True)
    y_train = pd.concat(train_y_parts, ignore_index=True)
    X_test = pd.concat(test_X_parts, ignore_index=True)
    y_test = pd.concat(test_y_parts, ignore_index=True)

    mask_tr = ~(X_train.isna().any(axis=1) | y_train.isna())
    mask_te = ~(X_test.isna().any(axis=1) | y_test.isna())
    X_train = X_train[mask_tr].reset_index(drop=True)
    y_train = y_train[mask_tr].reset_index(drop=True)
    X_test = X_test[mask_te].reset_index(drop=True)
    y_test = y_test[mask_te].reset_index(drop=True)

    print(f"\n📊 Train: {len(X_train)}  |  Test: {len(X_test)}")
    print(f"   Train pos: {y_train.mean()*100:.1f}%   Test pos: {y_test.mean()*100:.1f}%\n")

    # ---------- تست همه‌ی مدل‌ها ----------
    models = get_models()
    results = []

    print(f"{'='*80}")
    print(f"{'مدل':<25} {'Train AUC':>11} {'Test AUC':>11} {'Gap':>9} {'Time':>8}")
    print(f"{'='*80}")

    import time
    for name, model in models.items():
        try:
            start = time.time()
            model.fit(X_train, y_train)
            elapsed = time.time() - start

            train_auc = roc_auc_score(y_train, model.predict_proba(X_train)[:, 1])
            test_auc = roc_auc_score(y_test, model.predict_proba(X_test)[:, 1])
            gap = train_auc - test_auc

            results.append({
                "name": name,
                "train_auc": train_auc,
                "test_auc": test_auc,
                "gap": gap,
                "time": elapsed,
            })

            print(f"{name:<25} {train_auc:>11.4f} {test_auc:>11.4f} {gap:>+9.4f} {elapsed:>7.2f}s")
        except Exception as e:
            print(f"{name:<25} ❌ {e}")

    # ---------- برنده ----------
    if results:
        winner = max(results, key=lambda x: x["test_auc"])
        print(f"\n🏆 بهترین Test AUC: {winner['name']}")
        print(f"   Test AUC: {winner['test_auc']:.4f}")

        # کمترین Overfit
        least_overfit = min(results, key=lambda x: x["gap"])
        print(f"\n🎯 کمترین Overfit: {least_overfit['name']}")
        print(f"   Gap: {least_overfit['gap']:+.4f}")


if __name__ == "__main__":
    asyncio.run(main())
