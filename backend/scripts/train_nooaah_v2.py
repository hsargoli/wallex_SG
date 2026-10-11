"""Nooaah ML v2 — label قوی‌تر + feature متمرکز.

تفاوت با v1:
  - label: TP=4%، SL=2%، lookahead=48h (به‌جای 2/1.5/24)
  - features: 12 feature مخصوص Nooaah (نه 22 feature bottom-detection)
  - split: با gap=48 (جلوگیری از temporal leakage)
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
from app.domain.entities.candle import Candle
from app.infrastructure.exchange.wallex.client import WallexExchange
from app.services.bots.nooaah.bot import NooaahBot
from app.services.bots.nooaah.config import NooaahConfig
from app.domain.analysis.models.feature_math import (
    adx,
    atr_last,
    ema_last,
    rsi,
    trend_strength,
    volatility,
    volume_z,
)

MODEL_PATH = Path("data/models/nooaah_lgbm_v2.txt")
LOOKAHEAD = 48
TP_PCT = 4.0
SL_PCT = 2.0
TRAIN_PCT = 0.7
WINDOW = 24  # پنجره برای محاسبه‌ی feature ها


def candles_to_df(candles: list[Candle]) -> pd.DataFrame:
    return pd.DataFrame([
        {"time": c.time, "open": float(c.open), "high": float(c.high),
         "low": float(c.low), "close": float(c.close), "volume": float(c.volume)}
        for c in candles
    ])


def build_nooaah_features(df: pd.DataFrame) -> pd.DataFrame:
    """۱۲ feature مخصوص regime detection."""
    out = pd.DataFrame(index=df.index)
    closes = df["close"].values
    vols = df["volume"].values
    highs = df["high"].values
    lows = df["low"].values

    n = len(df)
    volatility_arr = np.full(n, np.nan)
    rsi_arr = np.full(n, np.nan)
    trend_arr = np.full(n, np.nan)
    vol_z_arr = np.full(n, np.nan)
    adx_arr = np.full(n, np.nan)
    atr_pct_arr = np.full(n, np.nan)
    ema_align_arr = np.full(n, 0)
    ret5_arr = np.full(n, np.nan)
    ret20_arr = np.full(n, np.nan)
    consec_up_arr = np.full(n, 0)
    near_high_arr = np.full(n, np.nan)
    near_low_arr = np.full(n, np.nan)

    for i in range(WINDOW, n):
        # candles window
        candles = [
            Candle(
                time=int(df["time"].iloc[j]),
                open=type(df["open"].iloc[j])(df["open"].iloc[j]),
                high=type(df["high"].iloc[j])(df["high"].iloc[j]),
                low=type(df["low"].iloc[j])(df["low"].iloc[j]),
                close=type(df["close"].iloc[j])(df["close"].iloc[j]),
                volume=type(df["volume"].iloc[j])(df["volume"].iloc[j]),
            )
            for j in range(max(0, i - 200), i + 1)
        ]
        window = candles[-WINDOW:]

        try:
            volatility_arr[i] = volatility(window)
            rsi_arr[i] = rsi(candles, 14)
            trend_arr[i] = trend_strength(window)
            vol_z_arr[i] = volume_z(window)
        except Exception:
            pass

        if len(candles) >= 100:
            try:
                adx_arr[i] = adx(candles, 14)
                atr_v = atr_last(candles, 14)
                atr_pct_arr[i] = (atr_v / closes[i] * 100) if closes[i] else 0
                ema20 = ema_last(candles, 20)
                ema50 = ema_last(candles, 50)
                ema100 = ema_last(candles, 100) if len(candles) >= 100 else 0
                if ema20 > ema50 > ema100:
                    ema_align_arr[i] = 1
                elif ema20 < ema50 < ema100:
                    ema_align_arr[i] = -1
            except Exception:
                pass

        if i >= 5:
            ret5_arr[i] = (closes[i] - closes[i - 5]) / closes[i - 5] * 100
        if i >= 20:
            ret20_arr[i] = (closes[i] - closes[i - 20]) / closes[i - 20] * 100

        # consecutive up
        cu = 0
        for j in range(i, max(0, i - 10), -1):
            if closes[j] > closes[j - 1]:
                cu += 1
            else:
                break
        consec_up_arr[i] = cu

        if i >= 20:
            hi20 = max(highs[i - 20 : i])
            lo20 = min(lows[i - 20 : i])
            if hi20 > lo20:
                near_high_arr[i] = (closes[i] - lo20) / (hi20 - lo20)
                near_low_arr[i] = 1 - near_high_arr[i]

    out["volatility"] = volatility_arr
    out["rsi"] = rsi_arr
    out["trend_strength"] = trend_arr
    out["volume_z"] = vol_z_arr
    out["adx"] = adx_arr
    out["atr_pct"] = atr_pct_arr
    out["ema_align"] = ema_align_arr
    out["ret_5"] = ret5_arr
    out["ret_20"] = ret20_arr
    out["consec_up"] = consec_up_arr
    out["near_high_20"] = near_high_arr
    out["near_low_20"] = near_low_arr

    return out


def build_label_v2(df: pd.DataFrame) -> pd.Series:
    """label=1 اگه تو lookahead، TP قبل SL خورد."""
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
            try:
                c = await uc.execute(symbol=sym, timeframe="1h", limit=limit)
                if c:
                    data[sym] = c
            except Exception as e:
                print(f"   ⚠️  {sym}: {str(e)[:60]}")
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
    print("📥 Fetching 1h...")
    data = await fetch_all(symbols, limit=700)
    print(f"   received {len(data)} series\n")

    train_X_parts, train_y_parts = [], []
    test_X_parts, test_y_parts = [], []

    for sym, candles in data.items():
        df = candles_to_df(candles)
        if len(df) < 300:
            continue
        X = build_nooaah_features(df)
        y = build_label_v2(df)

        mask = y.notna() & ~X.isna().any(axis=1)
        X = X[mask].reset_index(drop=True)
        y = y[mask].reset_index(drop=True)

        if len(X) < 100:
            continue

        n_train = int(len(X) * TRAIN_PCT)
        gap = LOOKAHEAD

        train_X_parts.append(X.iloc[:n_train])
        train_y_parts.append(y.iloc[:n_train])
        test_X_parts.append(X.iloc[n_train + gap:])
        test_y_parts.append(y.iloc[n_train + gap:])

        print(f"   {sym}: {len(X)} samples ({n_train} train / {len(X) - n_train - gap} test)")

    if not train_X_parts:
        print("❌ no data")
        return

    X_train = pd.concat(train_X_parts, ignore_index=True)
    y_train = pd.concat(train_y_parts, ignore_index=True)
    X_test = pd.concat(test_X_parts, ignore_index=True)
    y_test = pd.concat(test_y_parts, ignore_index=True)

    print(f"\n📊 train: {len(X_train)}, positive rate={y_train.mean():.2%}")
    print(f"📊 test:  {len(X_test)}, positive rate={y_test.mean():.2%}\n")

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

    print("🎯 Training LightGBM v2...")
    model = lgb.train(
        params,
        dtrain,
        num_boost_round=500,
        valid_sets=[dvalid],
        callbacks=[lgb.early_stopping(50, verbose=False)],
    )

    y_pred_prob = model.predict(X_test)
    y_pred = (y_pred_prob >= 0.5).astype(int)

    print(f"\n{'='*60}")
    print(f"  📊 Test metrics v2")
    print(f"{'='*60}")
    print(f"  AUC:       {roc_auc_score(y_test, y_pred_prob):.4f}")
    print(f"  Accuracy:  {accuracy_score(y_test, y_pred):.4f}")
    print(f"  Precision: {precision_score(y_test, y_pred, zero_division=0):.4f}")
    print(f"  Recall:    {recall_score(y_test, y_pred, zero_division=0):.4f}")

    imp = sorted(
        zip(model.feature_name(), model.feature_importance()),
        key=lambda x: x[1], reverse=True,
    )
    print(f"\n  Feature importance:")
    for name, score in imp:
        print(f"    {name:20} {score}")

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    model.save_model(str(MODEL_PATH))
    print(f"\n✅ Saved → {MODEL_PATH}")


if __name__ == "__main__":
    asyncio.run(main())
