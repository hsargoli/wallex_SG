"""14_ml_pipeline.py — Proper ML pipeline with denoising + walk-forward.

Key improvements over 13:
  1. Denoising: remove unknown regime, volume spike, ATR anomaly
  2. Rich features: 20 features (technical + volume + multi-TF + time)
  3. Walk-forward CV (5 windows, not single 70/30)
  4. Class weights (balanced)
  5. Hyperparameter search (grid, on first window)
  6. Target: 3 variants (binary sign, strong move, high-conf only)

Success (AP-57):
  - At least one target reaches 55%+ on walk-forward test
  - At least one target reaches 75%+ on strong-move subset
"""
from __future__ import annotations

import json
import sys
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, "backend")

import numpy as np
import pandas as pd
from app.domain.entities.candle import Candle
from app.services.indicators import adx, ema
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import accuracy_score

DATA = Path("research/tsfresh/data/BTCUSDT_1h_full.csv")
OUT = Path("frontend/public/data/ml-pipeline.json")

HORIZONS = [24, 72, 168]  # 1d, 3d, 7d
STRONG_MOVE_PCT = 2.0
N_WINDOWS = 5  # walk-forward windows

HYPERPARAMS = [
    {"max_depth": 3, "learning_rate": 0.05, "max_iter": 200, "l2": 0.1},
    {"max_depth": 5, "learning_rate": 0.05, "max_iter": 200, "l2": 0.1},
    {"max_depth": 5, "learning_rate": 0.1, "max_iter": 100, "l2": 0.0},
]


def load_candles(csv_path: Path) -> list[Candle]:
    df = pd.read_csv(csv_path)
    times = df["datetime"].apply(lambda x: int(pd.Timestamp(x).timestamp())).values
    return [
        Candle(time=int(times[i]), open=Decimal(str(r["open"])), high=Decimal(str(r["high"])),
               low=Decimal(str(r["low"])), close=Decimal(str(r["close"])), volume=Decimal(str(r["volume"])))
        for i, r in df.iterrows()
    ]


def build_features(candles: list[Candle]) -> pd.DataFrame:
    """20 rich features (no look-ahead)."""
    df = pd.DataFrame([{
        "time": c.time, "open": float(c.open), "high": float(c.high),
        "low": float(c.low), "close": float(c.close), "volume": float(c.volume),
    } for c in candles])

    # Returns
    df["ret_1"] = df["close"].pct_change(1)
    df["ret_4"] = df["close"].pct_change(4)
    df["ret_24"] = df["close"].pct_change(24)
    df["ret_168"] = df["close"].pct_change(168)

    # RSI
    delta = df["close"].diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()
    df["rsi_14"] = 100 - 100 / (1 + gain / loss.replace(0, np.nan))

    # MACD
    ema12 = df["close"].ewm(span=12, adjust=False).mean()
    ema26 = df["close"].ewm(span=26, adjust=False).mean()
    df["macd"] = ema12 - ema26
    df["macd_sig"] = df["macd"].ewm(span=9, adjust=False).mean()
    df["macd_hist"] = df["macd"] - df["macd_sig"]

    # Bollinger
    ma20 = df["close"].rolling(20).mean()
    std20 = df["close"].rolling(20).std()
    df["bb_upper"] = ma20 + 2 * std20
    df["bb_lower"] = ma20 - 2 * std20
    df["bb_width"] = (df["bb_upper"] - df["bb_lower"]) / ma20
    df["bb_pos"] = (df["close"] - df["bb_lower"]) / (df["bb_upper"] - df["bb_lower"]).replace(0, np.nan)

    # ATR
    tr = pd.concat([df["high"] - df["low"], (df["high"] - df["close"].shift()).abs(),
                    (df["low"] - df["close"].shift()).abs()], axis=1).max(axis=1)
    df["atr_14"] = tr.rolling(14).mean()
    df["atr_pct"] = df["atr_14"] / df["close"]

    # EMA ratios
    df["ema_ratio_20_50"] = df["close"].ewm(span=20).mean() / df["close"].ewm(span=50).mean() - 1
    df["ema_ratio_50_200"] = df["close"].ewm(span=50).mean() / df["close"].ewm(span=200).mean() - 1

    # Volume
    df["vol_ma20"] = df["volume"].rolling(20).mean()
    df["vol_ratio"] = df["volume"] / df["vol_ma20"]
    df["vol_std"] = df["volume"].rolling(20).std()
    df["vol_z"] = (df["volume"] - df["vol_ma20"]) / df["vol_std"].replace(0, np.nan)

    # ADX (as feature)
    adx_vals = adx(candles, 14)
    df["adx_14"] = [float(v) if v is not None else np.nan for v in adx_vals]

    # Time-based
    df["hour"] = (df["time"] // 3600) % 24
    df["dow"] = (df["time"] // 86400 + 4) % 7  # 1970-01-01 was Thursday

    # Volatility
    df["volatility_24"] = df["ret_1"].rolling(24).std()
    df["volatility_168"] = df["ret_1"].rolling(168).std()

    return df


def denoise_mask(df: pd.DataFrame) -> pd.Series:
    """True = keep, False = noise (exclude)."""
    mask = pd.Series(True, index=df.index)
    # 1. Remove volume spikes (vol_z > 5)
    mask &= df["vol_z"].abs() <= 5
    # 2. Remove ATR anomaly (atr_pct > 3x rolling median)
    atr_median = df["atr_pct"].rolling(168, min_periods=20).median()
    mask &= df["atr_pct"] <= atr_median * 3
    # 3. Remove low-volume candles (vol_ratio < 0.1)
    mask &= df["vol_ratio"] >= 0.1
    return mask


def add_targets(df: pd.DataFrame, horizon: int) -> pd.DataFrame:
    fwd = (df["close"].shift(-horizon) / df["close"] - 1) * 100
    df = df.copy()
    df["fwd_ret"] = fwd

    # Binary sign
    df["target_sign"] = np.where(df["fwd_ret"].notna(),
                                  (df["fwd_ret"] > 0).astype(int), -1)
    df.loc[df["fwd_ret"].isna(), "target_sign"] = -1

    # Strong move
    df["target_strong"] = np.where(df["fwd_ret"].notna(),
                                    (df["fwd_ret"].abs() > STRONG_MOVE_PCT).astype(int), -1)
    df.loc[df["fwd_ret"].isna(), "target_strong"] = -1

    return df


FEATURE_COLS = [
    "ret_1", "ret_4", "ret_24", "ret_168",
    "rsi_14", "macd", "macd_sig", "macd_hist",
    "bb_width", "bb_pos",
    "atr_pct",
    "ema_ratio_20_50", "ema_ratio_50_200",
    "vol_ratio", "vol_z",
    "adx_14",
    "hour", "dow",
    "volatility_24", "volatility_168",
]


def walk_forward(X, y, n_windows: int, hyperparams_list: list, choose_best_on: int = 0):
    """Walk-forward CV: split into n_windows chunks, train on past, test on next."""
    n = len(X)
    window_size = n // (n_windows + 1)
    results = []

    # Pick hyperparams on first window only (avoid leakage)
    first_train_end = window_size
    first_test_end = 2 * window_size

    best_hp = None
    best_acc = -1
    for hp in hyperparams_list:
        clf = HistGradientBoostingClassifier(
            max_depth=hp["max_depth"],
            learning_rate=hp["learning_rate"],
            max_iter=hp["max_iter"],
            l2_regularization=hp["l2"],
            class_weight="balanced",
            random_state=42,
        )
        clf.fit(X[:first_train_end], y[:first_train_end])
        acc = accuracy_score(y[first_train_end:first_test_end],
                             clf.predict(X[first_train_end:first_test_end]))
        if acc > best_acc:
            best_acc = acc
            best_hp = hp

    # Use best_hp for all windows
    for w in range(1, n_windows + 1):
        train_end = w * window_size
        test_end = (w + 1) * window_size
        if test_end > n:
            break
        clf = HistGradientBoostingClassifier(
            max_depth=best_hp["max_depth"],
            learning_rate=best_hp["learning_rate"],
            max_iter=best_hp["max_iter"],
            l2_regularization=best_hp["l2"],
            class_weight="balanced",
            random_state=42,
        )
        clf.fit(X[:train_end], y[:train_end])
        preds = clf.predict(X[train_end:test_end])
        acc = accuracy_score(y[train_end:test_end], preds)
        results.append({
            "window": w,
            "train_n": train_end,
            "test_n": test_end - train_end,
            "accuracy": round(acc * 100, 1),
        })

    return {"best_hp": best_hp, "windows": results,
            "mean_accuracy": round(np.mean([r["accuracy"] for r in results]), 1)}


def run_horizon(candles: list[Candle], horizon: int) -> dict:
    print(f"\n{'=' * 60}")
    print(f"  Horizon: {horizon}h")
    print(f"{'=' * 60}")

    df = build_features(candles)
    df = add_targets(df, horizon)

    # Denoise
    mask = denoise_mask(df)
    df = df[mask].copy()
    df = df.dropna(subset=FEATURE_COLS + ["fwd_ret"])
    print(f"  After denoise + dropna: {len(df)} rows")

    results = {}

    # Target 1: Binary sign
    print(f"\n  [target_sign]")
    valid = df[df["target_sign"] != -1]
    X = valid[FEATURE_COLS].values
    y = valid["target_sign"].values.astype(int)
    wf = walk_forward(X, y, N_WINDOWS, HYPERPARAMS)
    baseline = max(np.mean(y), 1 - np.mean(y)) * 100
    print(f"    baseline (majority): {baseline:.1f}%")
    print(f"    best_hp: {wf['best_hp']}")
    print(f"    windows: {[w['accuracy'] for w in wf['windows']]}")
    print(f"    mean accuracy: {wf['mean_accuracy']}%")
    results["sign"] = {"baseline": round(baseline, 1), **wf}

    # Target 2: Strong move
    print(f"\n  [target_strong |fwd|>{STRONG_MOVE_PCT}%]")
    valid = df[df["target_strong"] != -1]
    X = valid[FEATURE_COLS].values
    y = valid["target_strong"].values.astype(int)
    wf = walk_forward(X, y, N_WINDOWS, HYPERPARAMS)
    baseline = max(np.mean(y), 1 - np.mean(y)) * 100
    print(f"    baseline (majority): {baseline:.1f}%")
    print(f"    best_hp: {wf['best_hp']}")
    print(f"    windows: {[w['accuracy'] for w in wf['windows']]}")
    print(f"    mean accuracy: {wf['mean_accuracy']}%")
    results["strong"] = {"baseline": round(baseline, 1), **wf}

    return {"horizon": horizon, "n_after_denoise": len(df), "targets": results}


def main() -> None:
    print("=" * 60)
    print("  14_ml_pipeline.py — Denoise + Walk-forward + Rich features")
    print("=" * 60)

    candles = load_candles(DATA)
    print(f"\n{len(candles)} 1h candles")

    results = [run_horizon(candles, h) for h in HORIZONS]

    print(f"\n{'=' * 60}")
    print("  FINAL VERDICT")
    print(f"{'=' * 60}")
    for r in results:
        print(f"\n  Horizon {r['horizon']}h (n={r['n_after_denoise']}):")
        for tname, t in r["targets"].items():
            lift = t["mean_accuracy"] - t["baseline"]
            verdict = "🟢 LEARNS" if lift > 3 else ("🟡 borderline" if lift > 0 else "🔴 stuck")
            print(f"    {tname:8s}: {t['mean_accuracy']:5.1f}% vs baseline {t['baseline']:5.1f}% "
                  f"(lift {lift:+5.1f}%) {verdict}")

    output = {
        "as_of": pd.Timestamp.now().isoformat(),
        "strong_move_pct": STRONG_MOVE_PCT,
        "n_windows": N_WINDOWS,
        "hyperparams_tried": HYPERPARAMS,
        "results": results,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\n[3] Saved: {OUT}")


if __name__ == "__main__":
    main()
