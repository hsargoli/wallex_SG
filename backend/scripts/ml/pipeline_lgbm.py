"""Pipeline: آموزش با LightGBM + مقایسه با Random Forest."""

import asyncio

import lightgbm as lgb
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


async def main():
    print(f"📥 دریافت {len(SYMBOLS)} نماد × {TF}...\n")
    markets_data = await fetch_all()

    train_X_parts, train_y_parts = [], []
    test_X_parts, test_y_parts = [], []

    for symbol, candles in markets_data.items():
        df = candles_to_df(candles)
        if len(df) < 200:
            continue
        X = build_features(df)
        y = build_label(df)
        n = len(X)
        split = int(n * 0.6)
        train_X_parts.append(X.iloc[:split])
        train_y_parts.append(y.iloc[:split])
        test_X_parts.append(X.iloc[split:])
        test_y_parts.append(y.iloc[split:])
        print(f"  {symbol:10}  train={split:>5}  test={n-split:>5}")

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

    print(f"\n📊 Train: {len(X_train)}  |  Test: {len(X_test)}\n")

    results = {}

    # ---------- ۱. Random Forest ----------
    print("🌲 Random Forest...")
    import time
    start = time.time()
    rf = RandomForestClassifier(
        n_estimators=200, max_depth=6, min_samples_leaf=30,
        random_state=42, n_jobs=-1,
    )
    rf.fit(X_train, y_train)
    rf_time = time.time() - start

    rf_train_auc = roc_auc_score(y_train, rf.predict_proba(X_train)[:, 1])
    rf_test_auc = roc_auc_score(y_test, rf.predict_proba(X_test)[:, 1])
    results["RF"] = {
        "train_auc": rf_train_auc,
        "test_auc": rf_test_auc,
        "gap": rf_train_auc - rf_test_auc,
        "time": rf_time,
    }

    # ---------- ۲. LightGBM ----------
    print("⚡ LightGBM...")
    start = time.time()
    lgbm = lgb.LGBMClassifier(
        n_estimators=200, max_depth=5, num_leaves=15,
        min_child_samples=30, learning_rate=0.05,
        reg_alpha=0.1, reg_lambda=0.1,
        random_state=42, verbose=-1,
    )
    lgbm.fit(X_train, y_train)
    lgbm_time = time.time() - start

    lgbm_train_auc = roc_auc_score(y_train, lgbm.predict_proba(X_train)[:, 1])
    lgbm_test_auc = roc_auc_score(y_test, lgbm.predict_proba(X_test)[:, 1])
    results["LightGBM"] = {
        "train_auc": lgbm_train_auc,
        "test_auc": lgbm_test_auc,
        "gap": lgbm_train_auc - lgbm_test_auc,
        "time": lgbm_time,
    }

    # ---------- مقایسه ----------
    print(f"\n{'='*75}")
    print(f"{'مدل':<15} {'Train AUC':>12} {'Test AUC':>12} {'Gap':>10} {'Time':>10}")
    print(f"{'='*75}")
    for name, r in results.items():
        print(f"{name:<15} {r['train_auc']:>12.4f} {r['test_auc']:>12.4f} {r['gap']:>+10.4f} {r['time']:>9.2f}s")

    # بهترین
    best = max(results.items(), key=lambda x: x[1]["test_auc"])
    print(f"\n🏆 بهترین بر اساس Test AUC: {best[0]}")
    print(f"   Test AUC: {best[1]['test_auc']:.4f}")


if __name__ == "__main__":
    asyncio.run(main())
