"""04_similarity.py — Historical Similarity Analysis (Insight, not trading).

For the most recent 24-candle window:
- Extract 20 OHLCV-derived features
- Z-score normalize globally (across all windows)
- Find top-K most similar historical windows (cosine similarity)
- Compute forward 24h returns for each match
- Output: frontend/public/data/similarity.json

Key design choices (per CTO, 2026-11-03):
- Window: 24 candles (1 day pattern)
- 20 features (not 1554 — avoid overfit per tsfresh verdict)
- Global Z-score (not rolling — for comparable scale)
- Top 50 matches (N>30 per AP-58)
- Horizon 24h (intuitive)

CRITICAL: no lookahead. Historical windows must have t+24 already available.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

DATA = Path("research/tsfresh/data/BTCUSDT_1h_full.csv")
OUT = Path("frontend/public/data/similarity.json")

WINDOW = 24
HORIZON = 24
TOP_K = 50


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add 20 features per candle (not per window)."""
    df = df.copy().reset_index(drop=True)

    # Returns
    df["ret_1"] = df["close"].pct_change(1)

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
    df["vol_ma20"] = df["volume"].rolling(20).mean()
    df["vol_ratio"] = df["volume"] / df["vol_ma20"]

    # Wick/body
    df["upper_wick"] = (df["high"] - df[["open", "close"]].max(axis=1)) / df["close"]
    df["lower_wick"] = (df[["open", "close"]].min(axis=1) - df["low"]) / df["close"]
    df["body_ratio"] = (df["close"] - df["open"]).abs() / (df["high"] - df["low"]).replace(0, np.nan)

    return df


def window_features(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate per-window features (each row = one 24-candle window)."""
    out = pd.DataFrame(index=df.index)
    out["ret_1_mean"] = df["ret_1"].rolling(WINDOW).mean()
    out["ret_1_std"] = df["ret_1"].rolling(WINDOW).std()
    out["ret_24"] = df["close"].pct_change(WINDOW)
    out["rsi_14_mean"] = df["rsi_14"].rolling(WINDOW).mean()
    out["rsi_14_last"] = df["rsi_14"]
    out["atr_14_mean"] = df["atr_14"].rolling(WINDOW).mean()
    out["atr_14_std"] = df["atr_14"].rolling(WINDOW).std()
    out["atr_pct_mean"] = df["atr_pct"].rolling(WINDOW).mean()
    out["ema_ratio_mean"] = df["ema_ratio"].rolling(WINDOW).mean()
    out["macd_mean"] = df["macd"].rolling(WINDOW).mean()
    out["macd_hist_mean"] = df["macd_hist"].rolling(WINDOW).mean()
    out["vol_ratio_mean"] = df["vol_ratio"].rolling(WINDOW).mean()
    out["vol_ratio_std"] = df["vol_ratio"].rolling(WINDOW).std()
    out["volatility"] = df["ret_1"].rolling(WINDOW).std()
    out["close_position"] = (df["close"] - df["low"].rolling(WINDOW).min()) / (
        df["high"].rolling(WINDOW).max() - df["low"].rolling(WINDOW).min()
    ).replace(0, np.nan)
    out["hh_ll_ratio"] = (
        df["high"].rolling(WINDOW).max() - df["low"].rolling(WINDOW).min()
    ) / df["close"]
    out["upper_wick_mean"] = df["upper_wick"].rolling(WINDOW).mean()
    out["lower_wick_mean"] = df["lower_wick"].rolling(WINDOW).mean()
    out["body_ratio_mean"] = df["body_ratio"].rolling(WINDOW).mean()
    return out


def main() -> None:
    print("=" * 60)
    print("  04_similarity.py — Historical Similarity Analysis")
    print("=" * 60)
    print(f"Window={WINDOW}h, Horizon={HORIZON}h, TopK={TOP_K}")

    print(f"\n[1] Load: {DATA}")
    if not DATA.exists():
        raise SystemExit(f"❌ not found: {DATA}")
    df = pd.read_csv(DATA)
    df["datetime"] = pd.to_datetime(df["datetime"])
    df = df.sort_values("datetime").reset_index(drop=True)
    print(f"    {len(df)} rows | {df['datetime'].iloc[0]} → {df['datetime'].iloc[-1]}")

    print("\n[2] Add per-candle features")
    df = add_features(df)

    print("\n[3] Aggregate per-window")
    wf = window_features(df)
    # forward return over 24h, aligned at window end
    fwd_ret_24h = df["close"].shift(-HORIZON) / df["close"] - 1
    wf = wf.copy()
    wf["forward_ret_24h"] = fwd_ret_24h

    # drop rows with NaN in features or forward return
    feat_cols = [c for c in wf.columns if c != "forward_ret_24h"]
    valid = wf.dropna(subset=feat_cols + ["forward_ret_24h"]).copy()
    print(f"    {len(valid)} valid windows (from {len(wf)})")

    # current window = last row (needs its features, not its forward return)
    current_idx = wf.index[-1]
    if pd.isna(wf.loc[current_idx, feat_cols]).any():
        raise SystemExit(f"❌ current window has NaN features: {wf.loc[current_idx, feat_cols].to_dict()}")
    current_features_raw = wf.loc[current_idx, feat_cols].values.astype(float)

    # historical windows = valid (has forward return) — exclude last HORIZON rows to avoid lookahead
    hist = valid[valid.index < current_idx].copy()
    print(f"    historical candidates: {len(hist)}")
    if len(hist) < TOP_K:
        raise SystemExit(f"❌ too few historical windows: {len(hist)} < {TOP_K}")

    # global Z-score over historical (mean/std from historical, applied to current too)
    mu = np.asarray(hist[feat_cols].mean().values, dtype=float).copy()
    sigma = np.asarray(hist[feat_cols].std().values, dtype=float).copy()
    sigma[sigma == 0] = 1.0  # avoid div by zero
    hist_norm = (hist[feat_cols].values - mu) / sigma
    current_norm = (current_features_raw - mu) / sigma

    print("\n[4] Compute cosine similarity")
    # cosine = dot(a,b) / (||a|| * ||b||)
    cur_norm_val = np.linalg.norm(current_norm)
    if cur_norm_val == 0:
        raise SystemExit("❌ current feature vector has zero norm")
    hist_norms = np.linalg.norm(hist_norm, axis=1)
    hist_norms[hist_norms == 0] = 1e-9
    sims = hist_norm @ current_norm / (hist_norms * cur_norm_val)
    hist["similarity"] = sims

    # top K
    top = hist.nlargest(TOP_K, "similarity")
    print(f"    top similarity: {top['similarity'].iloc[0]:.4f} → {top['similarity'].iloc[-1]:.4f}")

    print("\n[5] Build output")
    # current price
    current_price = float(df["close"].iloc[-1])
    current_datetime = str(df["datetime"].iloc[-1])
    current_regime = "unknown"  # placeholder; could enrich later

    similar_periods = []
    for _, row in top.iterrows():
        t = df["datetime"].iloc[int(row.name)]
        similar_periods.append({
            "date": t.isoformat(),
            "similarity": round(float(row["similarity"]), 4),
            "forward_return_24h_pct": round(float(row["forward_ret_24h"]) * 100, 2),
        })

    returns = top["forward_ret_24h"].values * 100
    stats = {
        "n": int(len(top)),
        "mean_return_24h_pct": round(float(returns.mean()), 2),
        "median_return_24h_pct": round(float(np.median(returns)), 2),
        "std_return_24h_pct": round(float(returns.std()), 2),
        "positive_pct": round(float((returns > 0).mean() * 100), 1),
        "min_return_24h_pct": round(float(returns.min()), 2),
        "max_return_24h_pct": round(float(returns.max()), 2),
    }

    current_features_dict = {
        col: round(float(v), 4) if not np.isnan(v) else None
        for col, v in zip(feat_cols, current_features_raw)
    }

    output = {
        "as_of": datetime.now(timezone.utc).isoformat(),
        "current_datetime": current_datetime,
        "current_price": current_price,
        "current_regime": current_regime,
        "window_hours": WINDOW,
        "horizon_hours": HORIZON,
        "n_features": len(feat_cols),
        "feature_names": feat_cols,
        "current_features": current_features_dict,
        "similar_periods": similar_periods,
        "stats": stats,
        "disclaimer": "Historical similarity analysis, not trading signal. N matches > 30 required (AP-58). Past patterns may not repeat.",
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\n[6] Saved: {OUT}")
    print(f"    {len(similar_periods)} similar periods")
    print(f"    stats: mean={stats['mean_return_24h_pct']}% median={stats['median_return_24h_pct']}% positive={stats['positive_pct']}%")
    print("\n✅ DONE")


if __name__ == "__main__":
    main()
