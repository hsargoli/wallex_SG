"""15_tsfresh_trading_backtest.py — Tsfresh Pre-Decision Backtest.

Logic:
  1. Window = 24h. Features = 19 (same as similarity page).
  2. For each hour i (from 200 onwards):
     - Find 5 most similar PAST windows (strictly before i - 24h to avoid look-ahead).
     - Check if ALL 5 have forward_return_24h > 0 (green).
     - If YES: Enter trade at close[i].
     - If NO: Log rejection (why?).
  3. Trade Exit: TP=3%, SL=3%, MaxHold=72h.
  4. Fees: 0.65% round-trip.
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
OUT = Path("frontend/public/data/tsfresh-backtest.json")

WINDOW = 24
N_MATCHES = 5
TP_PCT = 4.0
SL_PCT = 2.0
MAX_HOLD = 72
FEE_PCT = 0.65
GREEN_THRESHOLD = 1.5

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
    # Window features
    out = pd.DataFrame(index=df.index)
    out["ret_1_mean"] = df["ret_1"].rolling(WINDOW).mean()
    out["ret_1_std"] = df["ret_1"].rolling(WINDOW).std()
    out["ret_24"] = df["close"].pct_change(WINDOW)
    out["rsi_14_mean"] = df["rsi_14"].rolling(WINDOW).mean()
    out["rsi_14_last"] = df["rsi_14"]
    out["atr_14_mean"] = df["atr_pct"].rolling(WINDOW).mean()  # simplified
    out["atr_14_std"] = df["atr_pct"].rolling(WINDOW).std()
    out["atr_pct_mean"] = df["atr_pct"].rolling(WINDOW).mean()
    out["ema_ratio_mean"] = df["ema_ratio"].rolling(WINDOW).mean()
    out["macd_mean"] = df["macd"].rolling(WINDOW).mean()
    out["macd_hist_mean"] = df["macd_hist"].rolling(WINDOW).mean()
    out["vol_ratio_mean"] = df["volume"].rolling(WINDOW).mean() / df["volume"] # placeholder
    out["vol_ratio_std"] = df["volume"].rolling(WINDOW).std()
    out["volatility"] = df["ret_1"].rolling(WINDOW).std()
    out["close_position"] = (df["close"] - df["low"].rolling(WINDOW).min()) / (df["high"].rolling(WINDOW).max() - df["low"].rolling(WINDOW).min())
    out["hh_ll_ratio"] = (df["high"].rolling(WINDOW).max() - df["low"].rolling(WINDOW).min()) / df["close"]
    out["upper_wick_mean"] = 0.0 # simplified
    out["lower_wick_mean"] = 0.0
    out["body_ratio_mean"] = 0.0
    return out

def main():
    print("=" * 60)
    print("  15_tsfresh_trading_backtest.py")
    print("=" * 60)

    print(f"\n[1] Loading {DATA}")
    candles = load_candles(DATA)
    df = pd.DataFrame([{"open": float(c.open), "high": float(c.high), "low": float(c.low), "close": float(c.close), "volume": float(c.volume)} for c in candles])
    print(f"    {len(df)} candles")

    print(f"\n[2] Building features (window={WINDOW})")
    feats = build_features(df)
    fwd_ret = (df["close"].shift(-24) / df["close"] - 1) * 100
    fwd_ret = fwd_ret.replace([np.inf, -np.inf], np.nan)
    
    # dropna
    valid = feats.dropna().index
    feats = feats.loc[valid]
    fwd_ret = fwd_ret.loc[valid]
    df = df.loc[valid]
    print(f"    {len(feats)} valid windows")

    print(f"\n[3] Normalizing features")
    feats = feats.replace([np.inf, -np.inf], np.nan).fillna(0)
    
    mu = feats.mean().values.copy()
    sigma = feats.std().values.copy()
    sigma[sigma == 0] = 1.0
    
    X = (feats.values - mu) / sigma
    X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)
    
    X_norm = np.linalg.norm(X, axis=1, keepdims=True)
    X_norm[X_norm == 0] = 1e-9
    X_unit = X / X_norm

    print(f"\n[4] Running backtest loop")
    t0 = time.time()
    trades = []
    rejections = {"not_green": 0, "in_position": 0}
    in_position = False
    entry_idx = -1
    entry_price = 0.0
    
    closes = df["close"].values
    highs = df["high"].values
    lows = df["low"].values

    for i in range(200, len(df) - MAX_HOLD):
        # Trade management
        if in_position:
            # check TP, SL, timeout
            for t in range(entry_idx + 1, min(entry_idx + MAX_HOLD + 1, len(df))):
                if highs[t] >= entry_price * (1 + TP_PCT / 100):
                    exit_price = entry_price * (1 + TP_PCT / 100)
                    ret = TP_PCT - FEE_PCT
                    trades.append({"entry": i, "exit": t, "ret": ret, "reason": "TP"})
                    in_position = False
                    break
                elif lows[t] <= entry_price * (1 - SL_PCT / 100):
                    exit_price = entry_price * (1 - SL_PCT / 100)
                    ret = -SL_PCT - FEE_PCT
                    trades.append({"entry": i, "exit": t, "ret": ret, "reason": "SL"})
                    in_position = False
                    break
                elif t == entry_idx + MAX_HOLD:
                    exit_price = closes[t]
                    ret = (exit_price / entry_price - 1) * 100 - FEE_PCT
                    trades.append({"entry": i, "exit": t, "ret": ret, "reason": "Timeout"})
                    in_position = False
                    break
            if in_position:
                rejections["in_position"] += 1
                continue

        # Look for entry
        # only compare with past that has valid fwd_ret (i - 24)
        max_past = i - 24
        if max_past <= 0: continue

        sims = X_unit[i] @ X_unit[:max_past].T
        top5_idx = np.argsort(sims)[-N_MATCHES:]
        
        # check if all 5 are green
        all_green = all(fwd_ret.iloc[idx] > GREEN_THRESHOLD for idx in top5_idx)
        
        if all_green:
            in_position = True
            entry_idx = i
            entry_price = closes[i]
        else:
            rejections["not_green"] += 1

        if i % 5000 == 0:
            print(f"    [progress] {i} ticks, {len(trades)} trades in {time.time()-t0:.1f}s")

    # Analyze
    print(f"\n[5] Results")
    if trades:
        rets = np.array([t["ret"] for t in trades])
        wins = rets[rets > 0]
        losses = rets[rets <= 0]
        pf = wins.sum() / abs(losses.sum()) if losses.sum() != 0 else float("inf")
        wr = len(wins) / len(rets)
        
        # equity curve
        eq = [1.0]
        for r in rets:
            eq.append(eq[-1] * (1 + r / 100))
        peak = np.maximum.accumulate(eq)
        dd = (eq - peak) / peak
        max_dd = dd.min() * 100

        print(f"    Trades: {len(trades)}")
        print(f"    Win Rate: {wr*100:.1f}%")
        print(f"    Profit Factor: {pf:.2f}")
        print(f"    Total Return: {(eq[-1]-1)*100:.1f}%")
        print(f"    Max DD: {max_dd:.1f}%")
        print(f"    TP: {sum(1 for t in trades if t['reason']=='TP')}, SL: {sum(1 for t in trades if t['reason']=='SL')}, Timeout: {sum(1 for t in trades if t['reason']=='Timeout')}")
    else:
        print("    No trades generated.")
    
    print(f"\n    Rejections:")
    print(f"    - Not green (N<5): {rejections['not_green']}")
    print(f"    - In position: {rejections['in_position']}")

    # Save JSON for UI
    out = {
        "as_of": pd.Timestamp.now().isoformat(),
        "params": {"window": WINDOW, "N": N_MATCHES, "TP": TP_PCT, "SL": SL_PCT, "MaxHold": MAX_HOLD, "Fee": FEE_PCT},
        "stats": {
            "trades": len(trades),
            "win_rate": round(wr*100, 1) if trades else 0,
            "profit_factor": round(pf, 2) if trades else 0,
            "total_return": round((eq[-1]-1)*100, 1) if trades else 0,
            "max_dd": round(max_dd, 1) if trades else 0,
        },
        "trades": trades[-50:], # last 50 for UI
        "rejections": rejections
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(out, f, indent=2)
    print(f"\n[6] Saved: {OUT}")

if __name__ == "__main__":
    main()
