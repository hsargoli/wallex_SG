"""13_regime_balanced.py — ML with balanced targets (quantile + binary).

Hypothesis: previous ML (41.4%) was stuck on majority class (range 40.3%).
With balanced targets, ML should learn real patterns.

Targets:
  A. 3-class quantile (train-set q33, q67) → balanced 33/33/33
  B. Binary sign (up/down) → baseline ~50%
  C. Binary strong-move (|fwd| > threshold) → baseline maybe 20-30%

For each, compare:
  - Dummy (majority class)
  - ADX baseline
  - ML (HistGradientBoosting)

Success: ML > baseline + 5% on at least one target.
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
from app.services.bots.sarv_router.config import SarvRouterConfig
from app.services.indicators import adx, ema
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import accuracy_score

DATA = Path("research/tsfresh/data/BTCUSDT_1h_full.csv")
OUT = Path("frontend/public/data/regime-balanced.json")

TIMEFRAMES = [
    {"name": "1h/24h", "resample_hours": 1, "forward_bars": 24},
    {"name": "4h/10d", "resample_hours": 4, "forward_bars": 60},
]

STRONG_MOVE_PCT = 2.0  # |forward| > 2% = strong move


def load_candles(csv_path: Path) -> list[Candle]:
    df = pd.read_csv(csv_path)
    times = df["datetime"].apply(lambda x: int(pd.Timestamp(x).timestamp())).values
    return [
        Candle(time=int(times[i]), open=Decimal(str(r["open"])), high=Decimal(str(r["high"])),
               low=Decimal(str(r["low"])), close=Decimal(str(r["close"])), volume=Decimal(str(r["volume"])))
        for i, r in df.iterrows()
    ]


def resample_1h(candles: list[Candle], hours: int) -> list[Candle]:
    if hours == 1:
        return candles
    df = pd.DataFrame([{"datetime": pd.Timestamp(c.time, unit="s"),
                        "open": float(c.open), "high": float(c.high),
                        "low": float(c.low), "close": float(c.close),
                        "volume": float(c.volume)} for c in candles])
    df = df.set_index("datetime").resample(f"{hours}h").agg({
        "open": "first", "high": "max", "low": "min",
        "close": "last", "volume": "sum"
    }).dropna().reset_index()
    return [Candle(time=int(r["datetime"].timestamp()),
                   open=Decimal(str(r["open"])), high=Decimal(str(r["high"])),
                   low=Decimal(str(r["low"])), close=Decimal(str(r["close"])),
                   volume=Decimal(str(r["volume"]))) for _, r in df.iterrows()]


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    df["ret_1"] = df["close"].pct_change(1)
    df["ret_4"] = df["close"].pct_change(4)
    df["ret_24"] = df["close"].pct_change(24)
    delta = df["close"].diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()
    df["rsi"] = 100 - 100 / (1 + gain / loss.replace(0, np.nan))
    ema12 = df["close"].ewm(span=12, adjust=False).mean()
    ema26 = df["close"].ewm(span=26, adjust=False).mean()
    df["macd"] = ema12 - ema26
    df["macd_sig"] = df["macd"].ewm(span=9, adjust=False).mean()
    df["macd_hist"] = df["macd"] - df["macd_sig"]
    ma20 = df["close"].rolling(20).mean()
    std20 = df["close"].rolling(20).std()
    df["bb_width"] = (ma20 + 2 * std20 - (ma20 - 2 * std20)) / ma20
    df["bb_pos"] = (df["close"] - (ma20 - 2 * std20)) / (4 * std20)
    tr = pd.concat([df["high"] - df["low"], (df["high"] - df["close"].shift()).abs(),
                    (df["low"] - df["close"].shift()).abs()], axis=1).max(axis=1)
    df["atr_pct"] = tr.rolling(14).mean() / df["close"]
    df["ema_ratio"] = df["close"].ewm(span=20).mean() / df["close"].ewm(span=50).mean() - 1
    return df


def prepare_targets(df: pd.DataFrame, forward: int, train_end: int) -> dict:
    """Compute 3 different targets with proper train-set quantiles."""
    fwd = (df["close"].shift(-forward) / df["close"] - 1) * 100
    df = df.copy()
    df["fwd_ret"] = fwd

    # A. Quantile 3-class (from TRAIN only)
    train_fwd = df["fwd_ret"].iloc[:train_end].dropna()
    q33, q67 = train_fwd.quantile([0.33, 0.67])

    def classify3(r):
        if pd.isna(r):
            return None
        if r < q33:
            return 0  # down
        if r > q67:
            return 2  # up
        return 1  # range

    df["target_quantile"] = df["fwd_ret"].apply(classify3)

    # B. Binary sign
    def classify_binary(r):
        if pd.isna(r):
            return None
        return 1 if r > 0 else 0

    df["target_binary"] = df["fwd_ret"].apply(classify_binary)

    # C. Binary strong-move
    def classify_strong(r):
        if pd.isna(r):
            return None
        return 1 if abs(r) > STRONG_MOVE_PCT else 0

    df["target_strong"] = df["fwd_ret"].apply(classify_strong)

    return {"q33": float(q33), "q67": float(q67), "df": df}


def test_target(df: pd.DataFrame, feature_cols: list, target_col: str,
                train_end: int, adx_vals, ema_vals, config, forward: int) -> dict:
    """Test one target: dummy vs ADX vs ML."""
    valid = df.dropna(subset=[target_col] + feature_cols)
    X = valid[feature_cols].values
    y = valid[target_col].astype(int).values

    train_idx = valid.index[:train_end] if False else range(train_end)
    # use positional split
    n_train = sum(1 for i in valid.index if i < train_end)
    X_tr, X_te = X[:n_train], X[n_train:]
    y_tr, y_te = y[:n_train], y[n_train:]
    test_indices = [i for i in valid.index if i >= train_end]

    # Dummy (majority)
    if len(y_tr) == 0:
        return {"n_test": 0, "dummy_acc": 0, "adx_acc": 0, "ml_acc": 0}
    majority = int(np.bincount(y_tr).argmax())
    dummy_preds = np.full_like(y_te, majority)
    dummy_acc = accuracy_score(y_te, dummy_preds)

    # ADX baseline (map to target classes)
    adx_preds = []
    for idx in test_indices:
        adx_n = adx_vals[idx] if idx < len(adx_vals) else None
        ema_n = ema_vals[idx] if idx < len(ema_vals) else None
        price = float(df["close"].iloc[idx])
        if adx_n is None or ema_n is None:
            adx_preds.append(majority)
        elif adx_n > 25 and price > ema_n:
            adx_preds.append(2 if target_col == "target_quantile" else 1)
        elif adx_n > 25 and price < ema_n:
            adx_preds.append(0)
        else:
            adx_preds.append(1 if target_col == "target_quantile" else 0)
    adx_acc = accuracy_score(y_te, adx_preds[:len(y_te)])

    # ML
    if len(X_tr) < 100 or len(np.unique(y_tr)) < 2:
        ml_acc = 0
    else:
        clf = HistGradientBoostingClassifier(max_iter=100, max_depth=5,
                                             learning_rate=0.1, random_state=42)
        clf.fit(X_tr, y_tr)
        ml_preds = clf.predict(X_te)
        ml_acc = accuracy_score(y_te, ml_preds)

    return {
        "n_test": len(y_te),
        "majority_class": majority,
        "dummy_acc": round(dummy_acc * 100, 1),
        "adx_acc": round(adx_acc * 100, 1),
        "ml_acc": round(ml_acc * 100, 1),
        "ml_lift_over_dummy": round((ml_acc - dummy_acc) * 100, 1),
    }


def run_timeframe(candles_1h: list[Candle], tf: dict, config: SarvRouterConfig) -> dict:
    print(f"\n{'=' * 60}")
    print(f"  {tf['name']}")
    print(f"{'=' * 60}")

    candles = resample_1h(candles_1h, tf["resample_hours"])
    df = pd.DataFrame([{"open": float(c.open), "high": float(c.high),
                        "low": float(c.low), "close": float(c.close)} for c in candles])
    df = build_features(df)
    n = len(df)
    train_end = int(n * 0.7)

    targets = prepare_targets(df, tf["forward_bars"], train_end)
    df = targets["df"]
    print(f"  q33={targets['q33']:.3f}%, q67={targets['q67']:.3f}%")
    print(f"  train: {train_end}, test: {n - train_end}")

    adx_vals = adx(candles, config.adx_period)
    ema_vals = ema(candles, config.ema_period)
    feature_cols = ["ret_1", "ret_4", "ret_24", "rsi", "macd", "macd_hist",
                    "bb_width", "bb_pos", "atr_pct", "ema_ratio"]

    results = {}
    for name, col in [("quantile_3class", "target_quantile"),
                       ("binary_sign", "target_binary"),
                       ("binary_strong", "target_strong")]:
        r = test_target(df, feature_cols, col, train_end,
                        adx_vals, ema_vals, config, tf["forward_bars"])
        results[name] = r
        print(f"\n  [{name}]")
        print(f"    test n: {r['n_test']}")
        print(f"    dummy: {r['dummy_acc']}% | ADX: {r['adx_acc']}% | ML: {r['ml_acc']}%")
        print(f"    ML lift over dummy: {r['ml_lift_over_dummy']:+}%")

    return {"name": tf["name"], "targets": results}


def main() -> None:
    print("=" * 60)
    print("  13_regime_balanced.py — Balanced targets + ML")
    print("=" * 60)

    candles_1h = load_candles(DATA)
    print(f"\n{len(candles_1h)} 1h candles")

    config = SarvRouterConfig()
    results = [run_timeframe(candles_1h, tf, config) for tf in TIMEFRAMES]

    print(f"\n{'=' * 60}")
    print("  FINAL VERDICT")
    print(f"{'=' * 60}")
    for r in results:
        print(f"\n  {r['name']}:")
        for tname, t in r["targets"].items():
            verdict = "✅ ML learns" if t["ml_lift_over_dummy"] > 5 else "❌ ML stuck"
            print(f"    {tname:20s}: ML {t['ml_acc']:5.1f}% (vs dummy {t['dummy_acc']:5.1f}%, lift {t['ml_lift_over_dummy']:+5.1f}%) → {verdict}")

    output = {
        "as_of": pd.Timestamp.now().isoformat(),
        "strong_move_pct": STRONG_MOVE_PCT,
        "results": results,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\n[3] Saved: {OUT}")


if __name__ == "__main__":
    main()
