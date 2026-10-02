"""انتخاب بهترین feature ها."""

import asyncio

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_selection import mutual_info_classif, RFE
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score

from app.application.use_cases.get_candles import GetCandlesUseCase
from app.core.config import get_settings
from app.infrastructure.exchange.wallex.client import WallexExchange
from app.services.ml_bottom_model import build_features, candles_to_df


SYMBOLS = ["BTCTMN", "ETHTMN", "XRPTMN", "DOGETMN", "SOLTMN"]
TF = "15m"
N_CANDLES = 2000


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
    print(f"📥 دریافت {len(SYMBOLS)} نماد...\n")
    markets_data = await fetch_all()

    train_X, train_y = [], []
    test_X, test_y = [], []

    for symbol, candles in markets_data.items():
        df = candles_to_df(candles)
        if len(df) < 200:
            continue
        X = build_features(df)
        y = build_label(df)
        n = len(X)
        split = int(n * 0.6)
        train_X.append(X.iloc[:split])
        train_y.append(y.iloc[:split])
        test_X.append(X.iloc[split:])
        test_y.append(y.iloc[split:])

    X_train = pd.concat(train_X, ignore_index=True)
    y_train = pd.concat(train_y, ignore_index=True)
    X_test = pd.concat(test_X, ignore_index=True)
    y_test = pd.concat(test_y, ignore_index=True)

    mask_tr = ~(X_train.isna().any(axis=1) | y_train.isna())
    mask_te = ~(X_test.isna().any(axis=1) | y_test.isna())
    X_train = X_train[mask_tr].reset_index(drop=True)
    y_train = y_train[mask_tr].reset_index(drop=True)
    X_test = X_test[mask_te].reset_index(drop=True)
    y_test = y_test[mask_te].reset_index(drop=True)

    print(f"📊 Train: {len(X_train)}  |  Test: {len(X_test)}\n")

    # ---------- ۱. Mutual Information ----------
    print("="*70)
    print("📊 Mutual Information (کدوم feature واقعاً مرتبطه؟)")
    print("="*70)
    mi = mutual_info_classif(X_train, y_train, random_state=42)
    mi_series = pd.Series(mi, index=X_train.columns).sort_values(ascending=False)
    print("\n  Feature Importance (MI):")
    for name, val in mi_series.items():
        bar = "█" * int(val * 30)
        print(f"    {name:20} {val:.4f}  {bar}")

    # ---------- ۲. تست با feature های مختلف ----------
    print("\n" + "="*70)
    print("🧪 تست Logistic Regression با N feature برتر")
    print("="*70)

    top_features = mi_series.index.tolist()
    results = []

    for n in [3, 5, 7, 10, 15, 22]:
        feats = top_features[:n]

        model = LogisticRegression(max_iter=1000, C=0.1, random_state=42)
        model.fit(X_train[feats], y_train)

        train_auc = roc_auc_score(y_train, model.predict_proba(X_train[feats])[:, 1])
        test_auc = roc_auc_score(y_test, model.predict_proba(X_test[feats])[:, 1])
        gap = train_auc - test_auc

        marker = "⭐" if n == 5 else ""
        print(f"  {n:>2} feature:  Train={train_auc:.4f}  Test={test_auc:.4f}  Gap={gap:+.4f}  {marker}")
        results.append((n, test_auc, feats))

    # بهترین
    best_n, best_auc, best_feats = max(results, key=lambda x: x[1])
    print(f"\n🏆 بهترین: {best_n} feature → Test AUC = {best_auc:.4f}")
    print(f"   Featureها: {best_feats}")


if __name__ == "__main__":
    asyncio.run(main())
