"""آموزش مجدد با داده‌ی بیشتر + regularization."""

import asyncio

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


async def main():
    print(f"📥 دریافت {len(SYMBOLS)} نماد × {TF} (limit={N_CANDLES})...\n")
    markets_data = await fetch_all()

    # جمع آوری داده با تقسیم زمانی per-symbol
    train_X_parts, train_y_parts = [], []
    test_X_parts, test_y_parts = [], []

    for symbol, candles in markets_data.items():
        df = candles_to_df(candles)
        if len(df) < 200:
            continue

        X = build_features(df)
        y = build_label(df)

        # تقسیم زمانی 60/40
        n = len(X)
        split = int(n * 0.6)

        train_X_parts.append(X.iloc[:split])
        train_y_parts.append(y.iloc[:split])
        test_X_parts.append(X.iloc[split:])
        test_y_parts.append(y.iloc[split:])

        print(f"  {symbol:10}  total={n:>5}  train={split:>5}  test={n-split:>5}")

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
    print(f"   Train positive rate: {y_train.mean()*100:.1f}%")
    print(f"   Test  positive rate: {y_test.mean()*100:.1f}%\n")

    # چند مدل با regularization مختلف
    configs = [
        ("Depth=10, Leaf=10", dict(max_depth=10, min_samples_leaf=10, max_features="sqrt")),
        ("Depth=6,  Leaf=30", dict(max_depth=6, min_samples_leaf=30, max_features=8)),
        ("Depth=5,  Leaf=50", dict(max_depth=5, min_samples_leaf=50, max_features=5)),
        ("Depth=4,  Leaf=100", dict(max_depth=4, min_samples_leaf=100, max_features=4)),
    ]

    print(f"{'='*80}")
    print(f"{'مدل':<22} {'Train Acc':>10} {'Train AUC':>10} {'Test Acc':>10} {'Test AUC':>10} {'Gap':>8}")
    print(f"{'='*80}")

    best = None
    for name, params in configs:
        model = RandomForestClassifier(
            n_estimators=200,
            random_state=42,
            n_jobs=-1,
            **params,
        )
        model.fit(X_train, y_train)

        # Train
        pred_tr = model.predict(X_train)
        prob_tr = model.predict_proba(X_train)[:, 1]
        acc_tr = accuracy_score(y_train, pred_tr)
        auc_tr = roc_auc_score(y_train, prob_tr) if y_train.nunique() > 1 else 0

        # Test
        pred_te = model.predict(X_test)
        prob_te = model.predict_proba(X_test)[:, 1]
        acc_te = accuracy_score(y_test, pred_te)
        auc_te = roc_auc_score(y_test, prob_te) if y_test.nunique() > 1 else 0

        gap = auc_tr - auc_te

        print(f"{name:<22} {acc_tr:>10.4f} {auc_tr:>10.4f} {acc_te:>10.4f} {auc_te:>10.4f} {gap:>+8.4f}")

        if best is None or auc_te > best[2]:
            best = (name, model, auc_te, gap)

    print(f"\n🏆 بهترین بر اساس Test AUC: {best[0]}")
    print(f"   Test AUC: {best[2]:.4f}  |  Gap: {best[3]:+.4f}")


if __name__ == "__main__":
    asyncio.run(main())
