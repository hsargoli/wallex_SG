"""03_tsfresh.py — tsfresh features + HistGBM + Long-Short (per AP-57, AP-58).

Uses EfficientFCParameters (746 features), HistGradientBoostingClassifier,
symmetric Long-Short threshold (0.6/0.4), and horizon-based exit.

Key choices:
- min_timeshift=0 (include current row in features; no 24h lag)
- max_timeshift=720 (1h) / 30 (1D) — rolling history
- Feature selection: FDR on train only (no leakage)
- Exit criteria: PF>1.2, AUC>0.55, N>30 (AP-58)

Flags:
  --quick: 7-day max_ts + MinimalFCParameters (fast smoke test)
"""
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import accuracy_score, roc_auc_score
from tsfresh import extract_features, select_features
from tsfresh.feature_extraction import EfficientFCParameters, MinimalFCParameters
from tsfresh.utilities.dataframe_functions import roll_time_series

DATA_DIR = Path("research/tsfresh/data")
OUT_DIR = Path("research/tsfresh")

FEE = 0.002
SLIPPAGE = 0.001
SPREAD = 0.0005
ROUND_TRIP = 2 * FEE + 2 * SLIPPAGE + SPREAD  # 0.0065

TRAIN_END = "2024-06-30 23:59:59"
VAL_END = "2025-06-30 23:59:59"

MIN_TRADES = 30
AUC_TH = 0.55
PF_TH = 1.2

QUICK = "--quick" in sys.argv
if QUICK:
    FC = MinimalFCParameters()
    MAX_TS_H = 168
    MAX_TS_D = 14
    print("⚠️ QUICK MODE: MinimalFCParameters, max_ts=7d/14d")
else:
    FC = EfficientFCParameters()
    MAX_TS_H = 720
    MAX_TS_D = 30

CHUNKSIZE = 200
N_JOBS = 2

HORIZON_H = 4
HORIZON_D = 1
MIN_TS = 0


def _extract_cut_time(x):
    """Robust: tsfresh index may be tuple ('ID', time) or string 'ID_time'."""
    if isinstance(x, tuple):
        return int(x[1])
    s = str(x)
    if "_" in s:
        return int(s.rsplit("_", 1)[-1])
    return int(s)


def roll_extract(df, max_ts, label):
    """Roll df, extract features, return X indexed by cut_time (int)."""
    df = df.copy().reset_index(drop=True)
    df["id"] = "BTCUSDT"
    df["time"] = range(len(df))

    t0 = time.time()
    rolled = roll_time_series(
        df[["id", "time", "close", "volume"]],
        column_id="id", column_sort="time",
        max_timeshift=max_ts, min_timeshift=MIN_TS,
        n_jobs=N_JOBS, chunksize=CHUNKSIZE,
    )
    n_rolled = len(rolled)
    print(f"  [{label}] rolled: {n_rolled} rows in {time.time()-t0:.1f}s")

    t0 = time.time()
    X = extract_features(
        rolled, column_id="id", column_sort="time",
        default_fc_parameters=FC,
        n_jobs=N_JOBS, chunksize=CHUNKSIZE,
        disable_progressbar=True,
    )
    print(f"  [{label}] features: {X.shape} in {time.time()-t0:.1f}s")

    # Extract cut_time from index (id values like "BTCUSDT_123") BEFORE reset
    cut_times = X.index.map(_extract_cut_time)
    X = X.reset_index(drop=True)
    X["cut_time"] = cut_times.values
    X = X.set_index("cut_time").sort_index()
    X = X.replace([np.inf, -np.inf], np.nan)
    return X


def add_target(df, horizon):
    df = df.copy()
    df["future_close"] = df["close"].shift(-horizon)
    df["y"] = (df["future_close"] > df["close"]).astype(float)
    return df


def run_tf(df, tf_name, horizon, max_ts):
    print(f"\n{'=' * 60}")
    print(f"  {tf_name} (horizon={horizon}, max_ts={max_ts}, min_ts={MIN_TS})")
    print(f"{'=' * 60}")

    df = add_target(df, horizon)
    df["datetime"] = pd.to_datetime(df["datetime"])

    X = roll_extract(df, max_ts, tf_name)
    X = X.loc[X.index.intersection(df.index)]
    df_aligned = df.loc[X.index]

    combined = X.copy()
    combined["datetime"] = df_aligned["datetime"].values
    combined["close"] = df_aligned["close"].values
    combined["y"] = df_aligned["y"].values
    combined = combined.dropna(subset=["y"]).reset_index(drop=True)
    print(f"  combined: {len(combined)} rows")

    train = combined[combined["datetime"] <= TRAIN_END].reset_index(drop=True)
    val = combined[(combined["datetime"] > TRAIN_END) & (combined["datetime"] <= VAL_END)].reset_index(drop=True)
    test = combined[combined["datetime"] > VAL_END].reset_index(drop=True)
    print(f"  split: train={len(train)}, val={len(val)}, test={len(test)}")

    feat_cols = [c for c in combined.columns if c not in ("datetime", "close", "y")]

    print(f"  selecting features (FDR, candidates={len(feat_cols)})...")
    t0 = time.time()
    X_tr_filled = train[feat_cols].fillna(0)
    try:
        sel = select_features(X_tr_filled, train["y"], fdr_level=0.05)
        sel_cols = sel.columns.tolist()
    except Exception as e:
        print(f"    select_features failed: {e}")
        sel_cols = []
    if len(sel_cols) == 0:
        print(f"    ⚠️ 0 selected — fallback top-50 by variance")
        var = train[feat_cols].var().sort_values(ascending=False)
        sel_cols = var.head(50).index.tolist()
    print(f"    selected: {len(sel_cols)} in {time.time()-t0:.1f}s")

    print(f"  training HistGBM...")
    X_tr = train[sel_cols].fillna(0).values
    y_tr = train["y"].values.astype(int)
    model = HistGradientBoostingClassifier(
        max_iter=200, max_depth=6, learning_rate=0.05,
        min_samples_leaf=50, random_state=42,
    )
    t0 = time.time()
    model.fit(X_tr, y_tr)
    print(f"    trained in {time.time()-t0:.1f}s")

    results = {}
    for name, split in [("val", val), ("test", test)]:
        if len(split) == 0:
            continue
        X_sp = split[sel_cols].fillna(0).values
        proba = model.predict_proba(X_sp)[:, 1]
        y_true = split["y"].values.astype(int)

        acc = accuracy_score(y_true, (proba >= 0.5).astype(int))
        try:
            auc = roc_auc_score(y_true, proba)
        except ValueError:
            auc = float("nan")

        bt = backtest_ls(split, proba, horizon)
        results[name] = {
            "n": int(len(split)),
            "accuracy": round(float(acc), 4),
            "auc": round(float(auc), 4) if not np.isnan(auc) else None,
            "backtest": bt,
        }
        print(f"\n  [{name.upper()}] n={len(split)}")
        print(f"    Acc={acc:.4f} AUC={auc:.4f}")
        if "error" not in bt:
            print(f"    N={bt['n_trades']} (L={bt['n_long']}/S={bt['n_short']}) "
                  f"WR={bt['win_rate']} PF={bt['profit_factor']} "
                  f"Ret={bt['total_return']} DD={bt['max_dd']}")

    return {
        "timeframe": tf_name,
        "horizon": horizon,
        "n_candidates": len(feat_cols),
        "n_selected": len(sel_cols),
        "metrics": results,
    }


def backtest_ls(df, proba, horizon, th_high=0.6, th_low=0.4):
    closes = df["close"].values
    n = len(df)
    if n <= horizon:
        return {"error": "too few rows"}
    trades = []
    for i in range(n - horizon):
        p = proba[i]
        if p >= th_high:
            d = "long"
            g = closes[i + horizon] / closes[i] - 1
        elif p <= th_low:
            d = "short"
            g = (closes[i] - closes[i + horizon]) / closes[i]
        else:
            continue
        trades.append({"dir": d, "net": g - ROUND_TRIP})
    if not trades:
        return {"error": "no trades"}
    rets = np.array([t["net"] for t in trades])
    wins = rets[rets > 0]
    losses = rets[rets <= 0]
    pf = float(wins.sum() / abs(losses.sum())) if losses.sum() != 0 else float("inf")
    wr = float(len(wins) / len(rets))
    eq = np.cumprod(1 + rets)
    peak = np.maximum.accumulate(eq)
    dd = (eq - peak) / peak
    return {
        "n_trades": int(len(trades)),
        "n_long": sum(1 for t in trades if t["dir"] == "long"),
        "n_short": sum(1 for t in trades if t["dir"] == "short"),
        "win_rate": round(wr, 4),
        "profit_factor": round(pf, 4) if pf != float("inf") else "inf",
        "total_return": round(float(eq[-1] - 1), 4),
        "max_dd": round(float(dd.min()), 4),
        "avg_return": round(float(rets.mean()), 6),
    }


def main():
    print("=" * 60)
    print("  03_tsfresh.py — tsfresh + HistGBM + Long-Short")
    print("=" * 60)
    print(f"Cost: {ROUND_TRIP*100:.2f}% round-trip")
    print(f"Threshold (AP-58): PF>{PF_TH} AUC>{AUC_TH} N>{MIN_TRADES}")

    print(f"\nLoading: {DATA_DIR}/BTCUSDT_1h_full.csv")
    df_1h = pd.read_csv(DATA_DIR / "BTCUSDT_1h_full.csv")
    df_1h["datetime"] = pd.to_datetime(df_1h["datetime"])
    print(f"  {len(df_1h)} rows")

    r_1h = run_tf(df_1h.copy(), "1h", HORIZON_H, MAX_TS_H)

    print(f"\nResampling 1h → 1D...")
    df_1d = df_1h.set_index("datetime").resample("1D").agg({
        "open": "first", "high": "max", "low": "min",
        "close": "last", "volume": "sum",
    }).dropna().reset_index()
    print(f"  {len(df_1d)} daily")

    r_1D = run_tf(df_1d, "1D", HORIZON_D, MAX_TS_D)

    out = {
        "config": {
            "cost": ROUND_TRIP, "fc": "Efficient" if not QUICK else "Minimal",
            "chunksize": CHUNKSIZE, "n_jobs": N_JOBS,
            "max_ts_1h": MAX_TS_H, "max_ts_1D": MAX_TS_D, "min_ts": MIN_TS,
            "horizon_1h": HORIZON_H, "horizon_1D": HORIZON_D,
            "th_high": 0.6, "th_low": 0.4,
        },
        "results_1h": r_1h,
        "results_1D": r_1D,
    }
    out_path = OUT_DIR / "tsfresh_results.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False, default=str)
    print(f"\nSaved: {out_path}")

    print(f"\n{'=' * 60}")
    print("  VERDICT (AP-57 + AP-58)")
    print(f"{'=' * 60}")
    for r in (r_1h, r_1D):
        if "error" in r:
            print(f"  {r['timeframe']}: {r['error']}")
            continue
        for split in ("val", "test"):
            m = r["metrics"].get(split)
            if not m:
                continue
            bt = m["backtest"]
            if "error" in bt:
                print(f"  {r['timeframe']} {split}: {bt['error']}")
                continue
            auc = m.get("auc") or 0
            pf = bt["profit_factor"]
            pf_v = float(pf) if pf != "inf" else float("inf")
            n_tr = bt["n_trades"]
            ok = (pf_v > PF_TH) and (auc > AUC_TH) and (n_tr > MIN_TRADES)
            print(f"  {r['timeframe']:3s} {split:5s}: PF={pf_v:.2f} AUC={auc:.4f} N={n_tr} → "
                  f"{'✅ EDGE' if ok else '❌ FAIL'}")

    print("\n✅ DONE")


if __name__ == "__main__":
    main()
