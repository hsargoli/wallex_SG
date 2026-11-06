"""16_tsfresh_voting_test.py — Test 4 combinations of threshold + voting.

Matrix:
  1. threshold=0.0  , votes=5
  2. threshold=0.65 , votes=5
  3. threshold=0.65 , votes=4  (Hosein's idea)
  4. threshold=1.5  , votes=4
"""
from __future__ import annotations

import json
import sys
import time
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, "backend")

import numpy as np
import pandas as pd
from app.domain.entities.candle import Candle

DATA = Path("research/tsfresh/data/BTCUSDT_1h_full.csv")
OUT = Path("frontend/public/data/tsfresh-voting-test.json")

WINDOW = 24
N_MATCHES = 5
TP_PCT = 3.0
SL_PCT = 3.0
MAX_HOLD = 72
FEE_PCT = 0.65

CONFIGS = [
    {"name": "baseline (threshold=0, votes=5/5)", "threshold": 0.0,  "votes": 5},
    {"name": "strict (threshold=0.65, votes=5/5)", "threshold": 0.65, "votes": 5},
    {"name": "balanced (threshold=0.65, votes=4/5)", "threshold": 0.65, "votes": 4},
    {"name": "aggressive (threshold=1.5, votes=4/5)", "threshold": 1.5,  "votes": 4},
]


def load_candles(csv_path: Path) -> list[Candle]:
    df = pd.read_csv(csv_path)
    times = df["datetime"].apply(lambda x: int(pd.Timestamp(x).timestamp())).values
    return [
        Candle(time=int(times[i]), open=Decimal(str(r["open"])), high=Decimal(str(r["high"])),
               low=Decimal(str(r["low"])), close=Decimal(str(r["close"])), volume=Decimal(str(r["volume"])))
        for i, r in df.iterrows()
    ]


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    df["ret_1"] = df["close"].pct_change(1)
    df["ret_4"] = df["close"].pct_change(4)
    df["ret_24"] = df["close"].pct_change(24)
    delta = df["close"].diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()
    df["rsi_14"] = 100 - 100 / (1 + gain / loss.replace(0, np.nan))
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
    out = pd.DataFrame(index=df.index)
    out["ret_1_mean"] = df["ret_1"].rolling(WINDOW).mean()
    out["ret_1_std"] = df["ret_1"].rolling(WINDOW).std()
    out["ret_24"] = df["close"].pct_change(WINDOW)
    out["rsi_14_mean"] = df["rsi_14"].rolling(WINDOW).mean()
    out["rsi_14_last"] = df["rsi_14"]
    out["atr_14_mean"] = df["atr_pct"].rolling(WINDOW).mean()
    out["atr_14_std"] = df["atr_pct"].rolling(WINDOW).std()
    out["atr_pct_mean"] = df["atr_pct"].rolling(WINDOW).mean()
    out["ema_ratio_mean"] = df["ema_ratio"].rolling(WINDOW).mean()
    out["macd_mean"] = df["macd"].rolling(WINDOW).mean()
    out["macd_hist_mean"] = df["macd_hist"].rolling(WINDOW).mean()
    out["vol_ratio_mean"] = df["volume"].rolling(WINDOW).mean() / df["volume"]
    out["vol_ratio_std"] = df["volume"].rolling(WINDOW).std()
    out["volatility"] = df["ret_1"].rolling(WINDOW).std()
    out["close_position"] = (df["close"] - df["low"].rolling(WINDOW).min()) / (df["high"].rolling(WINDOW).max() - df["low"].rolling(WINDOW).min())
    out["hh_ll_ratio"] = (df["high"].rolling(WINDOW).max() - df["low"].rolling(WINDOW).min()) / df["close"]
    out["upper_wick_mean"] = 0.0
    out["lower_wick_mean"] = 0.0
    out["body_ratio_mean"] = 0.0
    return out


def run_config(df, closes, highs, lows, fwd_ret, X_unit, threshold: float, votes: int) -> dict:
    trades = []
    in_position = False
    entry_idx = -1
    entry_price = 0.0
    rejections = 0
    candidates = 0

    for i in range(200, len(df) - MAX_HOLD):
        if in_position:
            for t in range(entry_idx + 1, min(entry_idx + MAX_HOLD + 1, len(df))):
                if highs[t] >= entry_price * (1 + TP_PCT / 100):
                    ret = TP_PCT - FEE_PCT
                    trades.append({"ret": ret, "reason": "TP"})
                    in_position = False
                    break
                elif lows[t] <= entry_price * (1 - SL_PCT / 100):
                    ret = -SL_PCT - FEE_PCT
                    trades.append({"ret": ret, "reason": "SL"})
                    in_position = False
                    break
                elif t == entry_idx + MAX_HOLD:
                    ret = (closes[t] / entry_price - 1) * 100 - FEE_PCT
                    trades.append({"ret": ret, "reason": "Timeout"})
                    in_position = False
                    break
            if in_position:
                continue

        max_past = i - 24
        if max_past <= 0:
            continue

        sims = X_unit[i] @ X_unit[:max_past].T
        top_idx = np.argsort(sims)[-N_MATCHES:]

        green_count = sum(1 for idx in top_idx if fwd_ret.iloc[idx] > threshold)
        candidates += 1

        if green_count >= votes:
            in_position = True
            entry_idx = i
            entry_price = closes[i]
        else:
            rejections += 1

    if not trades:
        return {"trades": 0, "win_rate": 0, "pf": 0, "total_return": 0, "max_dd": 0,
                "tp": 0, "sl": 0, "timeout": 0, "rejections": rejections, "candidates": candidates}

    rets = np.array([t["ret"] for t in trades])
    wins = rets[rets > 0]
    losses = rets[rets <= 0]
    pf = wins.sum() / abs(losses.sum()) if losses.sum() != 0 else 999
    wr = len(wins) / len(rets)

    eq = [1.0]
    for r in rets:
        eq.append(eq[-1] * (1 + r / 100))
    peak = np.maximum.accumulate(eq)
    dd = (eq - peak) / peak
    max_dd = dd.min() * 100

    return {
        "trades": len(trades),
        "win_rate": round(wr * 100, 1),
        "pf": round(pf, 2),
        "total_return": round((eq[-1] - 1) * 100, 1),
        "max_dd": round(max_dd, 1),
        "tp": sum(1 for t in trades if t["reason"] == "TP"),
        "sl": sum(1 for t in trades if t["reason"] == "SL"),
        "timeout": sum(1 for t in trades if t["reason"] == "Timeout"),
        "rejections": rejections,
        "candidates": candidates,
    }


def main() -> None:
    print("=" * 60)
    print("  16_tsfresh_voting_test.py")
    print("=" * 60)

    candles = load_candles(DATA)
    df = pd.DataFrame([{"open": float(c.open), "high": float(c.high),
                        "low": float(c.low), "close": float(c.close),
                        "volume": float(c.volume)} for c in candles])
    print(f"\n[1] {len(df)} candles")

    feats = build_features(df)
    fwd_ret = (df["close"].shift(-24) / df["close"] - 1) * 100
    fwd_ret = fwd_ret.replace([np.inf, -np.inf], np.nan)

    valid = feats.dropna().index
    feats = feats.loc[valid]
    fwd_ret = fwd_ret.loc[valid]
    df = df.loc[valid]
    feats = feats.replace([np.inf, -np.inf], np.nan).fillna(0)

    print(f"[2] {len(feats)} valid windows")

    mu = feats.mean().values.copy()
    sigma = feats.std().values.copy()
    sigma[sigma == 0] = 1.0
    X = (feats.values - mu) / sigma
    X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)
    X_norm = np.linalg.norm(X, axis=1, keepdims=True)
    X_norm[X_norm == 0] = 1e-9
    X_unit = X / X_norm

    closes = df["close"].values
    highs = df["high"].values
    lows = df["low"].values

    results = []
    for cfg in CONFIGS:
        print(f"\n[3] Testing: {cfg['name']}")
        t0 = time.time()
        r = run_config(df, closes, highs, lows, fwd_ret, X_unit, cfg["threshold"], cfg["votes"])
        elapsed = round(time.time() - t0, 1)
        print(f"    trades={r['trades']} | WR={r['win_rate']}% | PF={r['pf']} | "
              f"Ret={r['total_return']}% | DD={r['max_dd']}% | {elapsed}s")
        print(f"    TP={r['tp']}, SL={r['sl']}, Timeout={r['timeout']}, Rejections={r['rejections']}")
        results.append({**cfg, **r})

    print(f"\n{'=' * 60}")
    print("  SUMMARY")
    print(f"{'=' * 60}")
    print(f"{'Config':45s} | {'Trades':>7s} | {'WR%':>5s} | {'PF':>5s} | {'Ret%':>7s} | {'DD%':>6s}")
    for r in results:
        print(f"{r['name']:45s} | {r['trades']:7d} | {r['win_rate']:5.1f} | {r['pf']:5.2f} | "
              f"{r['total_return']:7.1f} | {r['max_dd']:6.1f}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump({"as_of": pd.Timestamp.now().isoformat(), "results": results}, f, indent=2)
    print(f"\n[4] Saved: {OUT}")


if __name__ == "__main__":
    main()
