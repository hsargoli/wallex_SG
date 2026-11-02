"""02_baseline.py — Baseline features + HistGradientBoosting + backtest.

Runs for BOTH timeframes:
- 1h: horizon=4 (4h ahead), target=classification (up/down)
- 1D: resample from 1h → daily, horizon=1

Features (per timeframe):
- RSI(14), ATR(14), ATR_pct
- EMA(20), EMA(50), EMA_ratio
- MACD, MACD_signal, MACD_hist
- Returns (1h, 4h, 24h) — or daily equivalents
- Volume ratio, volume pct

Model: HistGradientBoostingClassifier (sklearn — no LightGBM needed)

Backtest cost model (per Primer lesson 33):
- fee=0.2% each side = 0.4% round-trip
- slippage=0.1% each side = 0.2%
- spread=0.05% (half each side)
- total round-trip cost ≈ 0.65%
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import accuracy_score, roc_auc_score

DATA_DIR = Path("research/tsfresh/data")
OUT_DIR = Path("research/tsfresh")

# Cost model
FEE = 0.002          # 0.2% per side
SLIPPAGE = 0.001     # 0.1% per side
SPREAD = 0.0005      # 0.05% total

# ─── Features ────────────────────────────────────────────────────────
def add_features(df: pd.DataFrame) -> pd.DataFrame:
    """Compute trading features. Drops warmup NaNs at end."""
    df = df.copy().reset_index(drop=True)

    # Returns
    df["ret_1"] = df["close"].pct_change(1)
    df["ret_4"] = df["close"].pct_change(4)
    df["ret_24"] = df["close"].pct_change(24)

    # RSI(14)
    delta = df["close"].diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()
    rs = gain / loss.replace(0, np.nan)
    df["rsi_14"] = 100 - 100 / (1 + rs)

    # ATR(14)
    tr = pd.concat([
        df["high"] - df["low"],
        (df["high"] - df["close"].shift()).abs(),
        (df["low"] - df["close"].shift()).abs(),
    ], axis=1).max(axis=1)
    df["atr_14"] = tr.rolling(14).mean()
    df["atr_pct"] = df["atr_14"] / df["close"]

    # EMA
    df["ema_20"] = df["close"].ewm(span=20, adjust=False).mean()
    df["ema_50"] = df["close"].ewm(span=50, adjust=False).mean()
    df["ema_ratio"] = df["ema_20"] / df["ema_50"] - 1

    # MACD
    ema12 = df["close"].ewm(span=12, adjust=False).mean()
    ema26 = df["close"].ewm(span=26, adjust=False).mean()
    df["macd"] = ema12 - ema26
    df["macd_sig"] = df["macd"].ewm(span=9, adjust=False).mean()
    df["macd_hist"] = df["macd"] - df["macd_sig"]

    # Volume
    df["vol_ratio"] = df["volume"] / df["volume"].rolling(20).mean()
    df["vol_pct"] = df["volume"].pct_change(1)

    return df


FEATURE_COLS = [
    "ret_1", "ret_4", "ret_24",
    "rsi_14", "atr_pct", "ema_ratio",
    "macd", "macd_hist",
    "vol_ratio", "vol_pct",
]


# ─── Target ──────────────────────────────────────────────────────────
def add_target(df: pd.DataFrame, horizon: int) -> pd.DataFrame:
    df = df.copy()
    df["future_close"] = df["close"].shift(-horizon)
    df["y"] = (df["future_close"] > df["close"]).astype(int)
    return df


# ─── Resample 1h → 1D ────────────────────────────────────────────────
def resample_1d(df_1h: pd.DataFrame) -> pd.DataFrame:
    df = df_1h.copy()
    df["datetime"] = pd.to_datetime(df["datetime"])
    d = df.set_index("datetime").resample("1D").agg({
        "open": "first", "high": "max", "low": "min",
        "close": "last", "volume": "sum",
    }).dropna()
    return d.reset_index()


# ─── Backtest ────────────────────────────────────────────────────────
def backtest_long_only(df: pd.DataFrame, proba: np.ndarray, horizon: int,
                       threshold: float = 0.5) -> dict:
    """Long-only: enter at close[i] if proba[i]>=threshold, exit at close[i+horizon]."""
    n = len(df)
    if n <= horizon:
        return {"error": "too few samples"}

    closes = df["close"].values
    trades = []
    for i in range(n - horizon):
        if proba[i] >= threshold:
            entry = closes[i]
            exit_ = closes[i + horizon]
            gross = exit_ / entry - 1
            net = gross - 2 * FEE - 2 * SLIPPAGE - SPREAD
            trades.append(net)

    if not trades:
        return {"n_trades": 0, "win_rate": 0, "profit_factor": 0,
                "total_return": 0, "max_dd": 0, "avg_ret": 0}

    t = np.array(trades)
    wins = t[t > 0]
    losses = t[t <= 0]
    pf = float(wins.sum() / abs(losses.sum())) if losses.sum() != 0 else float("inf")
    wr = float(len(wins) / len(t))

    eq = np.cumprod(1 + t)
    peak = np.maximum.accumulate(eq)
    dd = (eq - peak) / peak
    max_dd = float(dd.min())

    return {
        "n_trades": int(len(t)),
        "win_rate": round(wr, 4),
        "profit_factor": round(pf, 4) if pf != float("inf") else "inf",
        "total_return": round(float(eq[-1] - 1), 4),
        "max_dd": round(max_dd, 4),
        "avg_ret": round(float(t.mean()), 6),
    }


# ─── Run one timeframe ───────────────────────────────────────────────
def run_tf(df: pd.DataFrame, tf_name: str, horizon: int) -> dict:
    print(f"\n{'=' * 60}")
    print(f"  {tf_name} (horizon={horizon})")
    print(f"{'=' * 60}")

    # Features
    df = add_features(df)
    df = add_target(df, horizon)
    df = df.dropna(subset=FEATURE_COLS + ["y"]).reset_index(drop=True)
    print(f"[1] Rows after feature NaN drop: {len(df)}")

    # Split (time-based)
    train = df[df["datetime"] <= "2024-06-30 23:59:59"].reset_index(drop=True)
    val = df[(df["datetime"] > "2024-06-30 23:59:59") & (df["datetime"] <= "2025-06-30 23:59:59")].reset_index(drop=True)
    test = df[df["datetime"] > "2025-06-30 23:59:59"].reset_index(drop=True)
    print(f"[2] Split: train={len(train)}, val={len(val)}, test={len(test)}")

    for name, s in (("train", train), ("val", val), ("test", test)):
        pos_rate = float(s["y"].mean()) if len(s) > 0 else 0
        print(f"    {name}: y=1 rate = {pos_rate:.3f}")

    # Train
    X_train = train[FEATURE_COLS].values
    y_train = train["y"].values
    model = HistGradientBoostingClassifier(
        max_iter=200, max_depth=6, learning_rate=0.05,
        min_samples_leaf=50, random_state=42, verbose=0,
    )
    t0 = time.time()
    model.fit(X_train, y_train)
    train_time = round(time.time() - t0, 2)
    print(f"[3] Model trained in {train_time}s")

    # Predict + evaluate
    results = {}
    for name, split_df in (("val", val), ("test", test)):
        if len(split_df) == 0:
            continue
        X = split_df[FEATURE_COLS].values
        y_true = split_df["y"].values
        proba = model.predict_proba(X)[:, 1]
        y_pred = (proba >= 0.5).astype(int)

        acc = accuracy_score(y_true, y_pred)
        try:
            auc = roc_auc_score(y_true, proba)
        except ValueError:
            auc = float("nan")

        bt = backtest_long_only(split_df, proba, horizon)

        results[name] = {
            "n": int(len(split_df)),
            "accuracy": round(float(acc), 4),
            "auc": round(float(auc), 4) if not np.isnan(auc) else None,
            "backtest": bt,
        }

        print(f"\n[4] {name.upper()} ({len(split_df)} rows)")
        print(f"    Accuracy: {acc:.4f} | AUC: {auc:.4f}")
        if "error" not in bt and bt["n_trades"] > 0:
            print(f"    Trades: {bt['n_trades']} | WinRate: {bt['win_rate']:.4f}")
            print(f"    PF: {bt['profit_factor']} | Return: {bt['total_return']:.4f}")
            print(f"    MaxDD: {bt['max_dd']:.4f} | AvgRet/trade: {bt['avg_ret']:.6f}")
        else:
            print(f"    ⚠️ No trades generated")

    return {
        "timeframe": tf_name,
        "horizon": horizon,
        "train_rows": int(len(train)),
        "val_rows": int(len(val)),
        "test_rows": int(len(test)),
        "train_time_sec": train_time,
        "metrics": results,
    }


# ─── Main ────────────────────────────────────────────────────────────
def main() -> None:
    print("=" * 60)
    print("  02_baseline.py — Baseline features + HistGBM + backtest")
    print("=" * 60)
    print(f"Cost model: fee={FEE*100:.2f}%/side, "
          f"slippage={SLIPPAGE*100:.1f}%/side, spread={SPREAD*100:.2f}%")

    # Load 1h full
    print(f"\nLoading: {DATA_DIR}/BTCUSDT_1h_full.csv")
    df_1h_full = pd.read_csv(DATA_DIR / "BTCUSDT_1h_full.csv")
    print(f"  {len(df_1h_full)} rows")

    # 1h
    result_1h = run_tf(df_1h_full.copy(), "1h", horizon=4)

    # 1D (resample)
    print(f"\nResampling 1h → 1D ...")
    df_1d = resample_1d(df_1h_full)
    print(f"  {len(df_1d)} daily candles")

    result_1D = run_tf(df_1d, "1D", horizon=1)

    # Summary
    print(f"\n{'=' * 60}")
    print("  SUMMARY")
    print(f"{'=' * 60}")
    print(f"{'TF':4s} | {'Rows (val/test)':16s} | {'AUC':6s} | {'PF':6s} | {'WR':6s} | {'DD':6s} | {'Trades':6s}")
    for r in (result_1h, result_1D):
        for split in ("val", "test"):
            m = r["metrics"].get(split)
            if not m:
                continue
            bt = m["backtest"]
            print(f"{r['timeframe']:4s} | {m['n']:5d}           | "
                  f"{m['auc']:.4f} | {bt['profit_factor']}  | "
                  f"{bt['win_rate']:.4f} | {bt['max_dd']:.4f} | {bt['n_trades']:5d}")

    # Exit criteria check
    print(f"\n{'=' * 60}")
    print("  EXIT CRITERIA (per di darya)")
    print(f"{'=' * 60}")
    for r in (result_1h, result_1D):
        test_m = r["metrics"].get("test", {})
        bt = test_m.get("backtest", {})
        pf = bt.get("profit_factor", 0)
        if pf == "inf":
            pf_val = float("inf")
        else:
            pf_val = float(pf) if pf else 0

        test_pf_ok = pf_val > 1.2
        test_wr_ok = bt.get("win_rate", 0) > 0.45
        test_dd_ok = bt.get("max_dd", -1) > -0.25

        print(f"{r['timeframe']}: PF={pf_val:.2f} (>1.2: {test_pf_ok}) | "
              f"WR={bt.get('win_rate', 0):.3f} (>0.45: {test_wr_ok}) | "
              f"DD={bt.get('max_dd', 0):.3f} (>-0.25: {test_dd_ok})")

    # Save results
    out = {
        "config": {
            "fee": FEE, "slippage": SLIPPAGE, "spread": SPREAD,
            "features": FEATURE_COLS,
        },
        "results_1h": result_1h,
        "results_1D": result_1D,
    }
    out_path = OUT_DIR / "baseline_results.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False, default=str)
    print(f"\nSaved: {out_path}")
    print("\n✅ DONE")


if __name__ == "__main__":
    main()
