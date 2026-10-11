"""Train Nooaah LightGBM classifier (binary: trending_up vs not).

Usage (from ~/wallex/backend):
    uv run python -m scripts.train_nooaah_classifier
"""

from __future__ import annotations

import asyncio
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    roc_auc_score,
)

from app.application.use_cases.get_candles import GetCandlesUseCase
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.infrastructure.exchange.wallex.client import WallexExchange
from app.services.bots.nooaah.bot import NooaahBot
from app.services.bots.nooaah.config import NooaahConfig
from app.services.ml_bottom_model import build_features, candles_to_df

MODEL_PATH = Path("data/models/nooaah_lgbm_v1.txt")
LOOKAHEAD = 24
TP_PCT = 2.0
SL_PCT = 1.5
TRAIN_PCT = 0.7


def build_label(df: pd.DataFrame) -> pd.Series:
    """label=1 اگه TP قبل SL خورد. NaN اگه هیچ‌کدوم."""
    labels: list[float] = []
    n = len(df)
    for i in range(n):
        if i + LOOKAHEAD >= n:
            labels.append(np.nan)
            continue
        entry = df["close"].iloc[i]
        tp = entry * (1 + TP_PCT / 100)
        sl = entry * (1 - SL_PCT / 100)
        future = df.iloc[i + 1 : i + LOOKAHEAD + 1]
        hit_tp = hit_sl = None
        for j, (_, row) in enumerate(future.iterrows()):
            if hit_sl is None and row["low"] <= sl:
                hit_sl = j
            if hit_tp is None and row["high"] >= tp:
                hit_tp = j
            if hit_tp is not None or hit_sl is not None:
                break
        if hit_tp is not None and (hit_sl is None or hit_tp < hit_sl):
            labels.append(1.0)
        elif hit_sl is not None:
            labels.append(0.0)
        else:
            labels.append(np.nan)
    return pd.Series(labels, index=df.index)


async def fetch_all(symbols: list[str], limit: int = 700):
    settings = get_settings()
    ex = WallexExchange.create(settings)
    try:
        uc = GetCandlesUseCase(exchange=ex)
        data = {}
        for sym in symbols:
            for tf in ("1h", "1D"):
                try:
                    c = await uc.execute(symbol=sym, timeframe=tf, limit=limit)
                    if c:
                        data[f"{sym}_{tf}"] = c
                except Exception as e:
                    print(f"   ⚠️  {sym} {tf}: {str(e)[:60]}")
        return data
    finally:
        await ex.aclose()


async def main() -> None:
    configure_logging()

    settings = get_settings()
    ex = WallexExchange.create(settings)
    try:
        bot = NooaahBot(exchange=ex, config=NooaahConfig())
        symbols = await bot.pick_top_symbols(8)
    finally:
        await ex.aclose()

    print(f"📥 Top symbols: {symbols}\n")
    print("📥 Fetching 1h + 1D...")
    data = await fetch_all(symbols, limit=700)
    print(f"   received {len(data)} series\n")

    train_X_parts, train_y_parts = [], []
    test_X_parts, test_y_parts = [], []

    for key, candles in data.items():
        df = candles_to_df(candles)
        if len(df) < 200:
            continue
        X = build_features(df)
        y = build_label(df)

        # drop NaN rows
        mask = y.notna() & ~X.isna().any(axis=1)
        X = X[mask]
        y = y[mask]

        if len(X) < 50:
            continue

        n_train = int(len(X) * TRAIN_PCT)
        train_X_parts.append(X.iloc[:n_train])
        train_y_parts.append(y.iloc[:n_train])
        test_X_parts.append(X.iloc[n_train:])
        test_y_parts.append(y.iloc[n_train:])

    if not train_X_parts:
        print("❌ no training data")
        return

    X_train = pd.concat(train_X_parts, ignore_index=True)
    y_train = pd.concat(train_y_parts, ignore_index=True)
    X_test = pd.concat(test_X_parts, ignore_index=True)
    y_test = pd.concat(test_y_parts, ignore_index=True)

    print(f"📊 train: {len(X_train)} samples, positive rate={y_train.mean():.2%}")
    print(f"📊 test:  {len(X_test)} samples, positive rate={y_test.mean():.2%}\n")

    params = {
        "objective": "binary",
        "metric": "auc",
        "learning_rate": 0.05,
        "num_leaves": 15,
        "min_data_in_leaf": 20,
        "feature_fraction": 0.8,
        "bagging_fraction": 0.8,
        "bagging_freq": 5,
        "verbose": -1,
        "seed": 42,
    }

    dtrain = lgb.Dataset(X_train, label=y_train)
    dvalid = lgb.Dataset(X_test, label=y_test, reference=dtrain)

    print("🎯 Training LightGBM...")
    model = lgb.train(
        params,
        dtrain,
        num_boost_round=500,
        valid_sets=[dvalid],
        callbacks=[lgb.early_stopping(50, verbose=False)],
    )

    # Evaluation
    y_pred_prob = model.predict(X_test)
    y_pred = (y_pred_prob >= 0.5).astype(int)

    print(f"\n{'='*60}")
    print(f"  📊 Test metrics")
    print(f"{'='*60}")
    print(f"  AUC:       {roc_auc_score(y_test, y_pred_prob):.4f}")
    print(f"  Accuracy:  {accuracy_score(y_test, y_pred):.4f}")
    print(f"  Precision: {precision_score(y_test, y_pred, zero_division=0):.4f}")
    print(f"  Recall:    {recall_score(y_test, y_pred, zero_division=0):.4f}")

    # Feature importance (top 10)
    imp = sorted(
        zip(model.feature_name(), model.feature_importance()),
        key=lambda x: x[1], reverse=True,
    )
    print(f"\n  Top 10 features:")
    for name, score in imp[:10]:
        print(f"    {name:20} {score}")

    # Save
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    model.save_model(str(MODEL_PATH))
    print(f"\n✅ Saved → {MODEL_PATH}")


if __name__ == "__main__":
    asyncio.run(main())
