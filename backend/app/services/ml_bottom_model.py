"""ML Bottom Model — Train / Save / Load / Predict."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier

from app.domain.entities.candle import Candle

MODEL_DIR = Path("data/models")
MODEL_PATH = MODEL_DIR / "bottom_model_v1.joblib"


# ---------- Feature Engineering ----------
def _rsi_series(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = (-delta.clip(upper=0)).rolling(period).mean()
    rs = gain / loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


FEATURE_NAMES = [
    "rsi",
    "rsi_lag1",
    "rsi_lag3",
    "rsi_change",
    "ret_1",
    "ret_3",
    "ret_5",
    "ma20_dist",
    "ma50_dist",
    "ma_cross",
    "pos_in_range",
    "near_low",
    "vol_ratio",
    "vol_ma_ratio",
    "body_ratio",
    "upper_wick",
    "lower_wick",
    "is_red",
    "consec_red",
    "atr_pct",
    "price_low_5",
    "rsi_low_5",
]


def candles_to_df(candles: list[Candle]) -> pd.DataFrame:
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
    out["rsi"] = _rsi_series(df["close"], 14)
    out["rsi_lag1"] = out["rsi"].shift(1)
    out["rsi_lag3"] = out["rsi"].shift(3)
    out["rsi_change"] = out["rsi"] - out["rsi"].shift(1)
    out["ret_1"] = df["close"].pct_change(1)
    out["ret_3"] = df["close"].pct_change(3)
    out["ret_5"] = df["close"].pct_change(5)
    ma20 = df["close"].rolling(20).mean()
    ma50 = df["close"].rolling(50).mean()
    out["ma20_dist"] = (df["close"] - ma20) / ma20
    out["ma50_dist"] = (df["close"] - ma50) / ma50
    out["ma_cross"] = (ma20 - ma50) / ma50
    high20 = df["high"].rolling(20).max()
    low20 = df["low"].rolling(20).min()
    rng = (high20 - low20).replace(0, np.nan)
    out["pos_in_range"] = (df["close"] - low20) / rng
    out["near_low"] = (df["low"] - low20) / rng
    vol_ma = df["volume"].rolling(20).mean()
    out["vol_ratio"] = df["volume"] / vol_ma.replace(0, np.nan)
    out["vol_ma_ratio"] = vol_ma / df["volume"].rolling(50).mean()
    hl = df["high"] - df["low"]
    out["body_ratio"] = (df["close"] - df["open"]).abs() / hl.replace(0, np.nan)
    out["upper_wick"] = (df["high"] - df[["open", "close"]].max(axis=1)) / hl.replace(0, np.nan)
    out["lower_wick"] = (df[["open", "close"]].min(axis=1) - df["low"]) / hl.replace(0, np.nan)
    out["is_red"] = (df["close"] < df["open"]).astype(int)
    red = (df["close"] < df["open"]).astype(int)
    out["consec_red"] = red.groupby((red != red.shift()).cumsum()).cumsum()
    out["atr_pct"] = hl / df["close"]
    out["price_low_5"] = df["low"].rolling(5).min() / df["low"]
    out["rsi_low_5"] = out["rsi"].rolling(5).min()
    return out


def build_label(
    df: pd.DataFrame, lookahead: int = 24, tp_pct: float = 1.5, sl_pct: float = 1.0
) -> pd.Series:
    labels = []
    for i in range(len(df)):
        if i + lookahead >= len(df):
            labels.append(np.nan)
            continue
        entry = df["close"].iloc[i]
        tp = entry * (1 + tp_pct / 100)
        sl = entry * (1 - sl_pct / 100)
        future = df.iloc[i + 1 : i + lookahead + 1]
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


# ---------- Training ----------
def train_model(markets_data: dict[str, list[Candle]]) -> RandomForestClassifier:
    """آموزش مدل روی چند نماد."""
    X_parts, y_parts = [], []
    for candles in markets_data.values():
        df = candles_to_df(candles)
        if len(df) < 100:
            continue
        X_parts.append(build_features(df))
        y_parts.append(build_label(df))

    if not X_parts:
        raise ValueError("داده کافی برای آموزش نیست")

    X = pd.concat(X_parts, ignore_index=True)
    y = pd.concat(y_parts, ignore_index=True)
    mask = ~(X.isna().any(axis=1) | y.isna())
    X_clean = X[mask].reset_index(drop=True)
    y_clean = y[mask].reset_index(drop=True)

    model = RandomForestClassifier(
        n_estimators=300,
        max_depth=10,
        min_samples_leaf=10,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X_clean, y_clean)
    return model


# ---------- Save / Load ----------
def save_model(model: RandomForestClassifier, path: Path | None = None) -> Path:
    import joblib

    path = path or MODEL_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, path)
    return path


def load_model(path: Path | None = None) -> RandomForestClassifier:
    import joblib

    path = path or MODEL_PATH
    if not path.exists():
        raise FileNotFoundError(f"مدل پیدا نشد: {path}")
    return joblib.load(path)


# ---------- Predict ----------
def predict_probability(
    model: RandomForestClassifier,
    candles: list[Candle],
) -> float | None:
    """احتمال کف بودن آخرین کندل (0-1)."""
    if len(candles) < 100:
        return None
    df = candles_to_df(candles)
    X = build_features(df)
    if X.empty:
        return None
    last = X.iloc[[-1]]
    if last.isna().any(axis=1).iloc[0]:
        return None
    prob = model.predict_proba(last)[0]
    return float(prob[1])
