"""12_regime_framework.py — Compare ADX, Voting, and ML for Regime Detection.

Output: frontend/public/data/regime-framework.json
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
OUT = Path("frontend/public/data/regime-framework.json")

TIMEFRAMES = [
    {"name": "1h/24h", "resample_hours": 1, "forward_bars": 24},
    {"name": "4h/10d", "resample_hours": 4, "forward_bars": 60},
]

def load_candles(csv_path: Path) -> list[Candle]:
    df = pd.read_csv(csv_path)
    times = df["datetime"].apply(lambda x: int(pd.Timestamp(x).timestamp())).values
    return [
        Candle(time=int(times[i]), open=Decimal(str(r["open"])), high=Decimal(str(r["high"])),
               low=Decimal(str(r["low"])), close=Decimal(str(r["close"])), volume=Decimal(str(r["volume"])))
        for i, r in df.iterrows()
    ]

def resample_1h(candles: list[Candle], hours: int) -> list[Candle]:
    if hours == 1: return candles
    df = pd.DataFrame([{"datetime": pd.Timestamp(c.time, unit="s"), "open": float(c.open), "high": float(c.high),
                        "low": float(c.low), "close": float(c.close), "volume": float(c.volume)} for c in candles])
    df = df.set_index("datetime").resample(f"{hours}h").agg({"open":"first","high":"max","low":"min","close":"last","volume":"sum"}).dropna().reset_index()
    return [Candle(time=int(r["datetime"].timestamp()), open=Decimal(str(r["open"])), high=Decimal(str(r["high"])),
                   low=Decimal(str(r["low"])), close=Decimal(str(r["close"])), volume=Decimal(str(r["volume"]))) for _, r in df.iterrows()]

def build_features(df: pd.DataFrame) -> pd.DataFrame:
    # returns
    df["ret_1"] = df["close"].pct_change(1)
    df["ret_4"] = df["close"].pct_change(4)
    df["ret_24"] = df["close"].pct_change(24)
    # rsi
    delta = df["close"].diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()
    df["rsi"] = 100 - 100 / (1 + gain/loss.replace(0, np.nan))
    # macd
    ema12 = df["close"].ewm(span=12, adjust=False).mean()
    ema26 = df["close"].ewm(span=26, adjust=False).mean()
    df["macd"] = ema12 - ema26
    df["macd_sig"] = df["macd"].ewm(span=9, adjust=False).mean()
    df["macd_hist"] = df["macd"] - df["macd_sig"]
    # bollinger
    ma20 = df["close"].rolling(20).mean()
    std20 = df["close"].rolling(20).std()
    df["bb_upper"] = ma20 + 2*std20
    df["bb_lower"] = ma20 - 2*std20
    df["bb_width"] = (df["bb_upper"] - df["bb_lower"]) / ma20
    df["bb_pos"] = (df["close"] - df["bb_lower"]) / (df["bb_upper"] - df["bb_lower"])
    # atr
    tr = pd.concat([df["high"]-df["low"], (df["high"]-df["close"].shift()).abs(), (df["low"]-df["close"].shift()).abs()], axis=1).max(axis=1)
    df["atr_pct"] = tr.rolling(14).mean() / df["close"]
    # ema_ratio
    df["ema_ratio"] = df["close"].ewm(span=20).mean() / df["close"].ewm(span=50).mean() - 1
    return df

def get_target(close: pd.Series, forward: int) -> pd.Series:
    future = close.shift(-forward)
    ret = (future / close - 1) * 100
    # 0=down, 1=range, 2=up
    target = np.where(ret > 1.0, 2, np.where(ret < -1.0, 0, 1))
    return pd.Series(target, index=close.index)

def run_timeframe(candles_1h: list[Candle], tf: dict, config: SarvRouterConfig):
    print(f"\n--- {tf['name']} ---")
    candles = resample_1h(candles_1h, tf["resample_hours"])
    df = pd.DataFrame([{"open": float(c.open), "high": float(c.high), "low": float(c.low), "close": float(c.close)} for c in candles])
    df = build_features(df)
    df["target"] = get_target(df["close"], tf["forward_bars"])
    df = df.dropna()

    feature_cols = ["ret_1", "ret_4", "ret_24", "rsi", "macd", "macd_hist", "bb_width", "bb_pos", "atr_pct", "ema_ratio"]
    X = df[feature_cols].values
    y = df["target"].values

    # Train/Test Split (70/30 Time-based)
    split_idx = int(len(df) * 0.7)
    X_train, X_test = X[:split_idx], X[split_idx:]
    y_train, y_test = y[:split_idx], y[split_idx:]

    # 1. ADX Baseline (on test set)
    adx_vals = adx(candles, config.adx_period)
    ema_vals = ema(candles, config.ema_period)
    base_preds = []
    for i in range(split_idx, len(df)):
        adx_n, ema_n, price = adx_vals[i], ema_vals[i], df["close"].iloc[i]
        if adx_n is None or ema_n is None: base_preds.append(1); continue
        if adx_n > 25 and price > ema_n: base_preds.append(2)
        elif adx_n > 25 and price < ema_n: base_preds.append(0)
        else: base_preds.append(1)
    adx_acc = accuracy_score(y_test, base_preds)

    # 2. Voting (RSI + MACD + BB)
    vote_preds = []
    for i in range(split_idx, len(df)):
        r = df["rsi"].iloc[i]; m = df["macd_hist"].iloc[i]; b = df["bb_pos"].iloc[i]
        votes = 0
        if r > 55: votes += 1
        elif r < 45: votes -= 1
        if m > 0: votes += 1
        elif m < 0: votes -= 1
        if b > 0.8: votes += 1
        elif b < 0.2: votes -= 1
        
        if votes >= 2: vote_preds.append(2)
        elif votes <= -2: vote_preds.append(0)
        else: vote_preds.append(1)
    vote_acc = accuracy_score(y_test, vote_preds)

    # 3. ML (HistGradientBoosting)
    clf = HistGradientBoostingClassifier(max_iter=100, max_depth=5, learning_rate=0.1, random_state=42)
    clf.fit(X_train, y_train)
    ml_preds = clf.predict(X_test)
    ml_acc = accuracy_score(y_test, ml_preds)

    print(f"  Test samples: {len(y_test)}")
    print(f"  ADX Baseline Accuracy: {adx_acc*100:.1f}%")
    print(f"  Voting (RSI/MACD/BB):  {vote_acc*100:.1f}%")
    print(f"  ML (HistGBM):          {ml_acc*100:.1f}%")

    return {
        "name": tf["name"],
        "test_samples": len(y_test),
        "adx_accuracy": round(adx_acc*100, 1),
        "voting_accuracy": round(vote_acc*100, 1),
        "ml_accuracy": round(ml_acc*100, 1)
    }

def main():
    print("=" * 60)
    print("  12_regime_framework.py — ADX vs Voting vs ML")
    print("=" * 60)

    candles_1h = load_candles(DATA)
    config = SarvRouterConfig()

    results = [run_timeframe(candles_1h, tf, config) for tf in TIMEFRAMES]

    print("\n" + "=" * 60)
    print("  FINAL VERDICT (on Test Set)")
    print("=" * 60)
    for r in results:
        print(f"  {r['name']:10s} | ADX: {r['adx_accuracy']:5.1f}% | Voting: {r['voting_accuracy']:5.1f}% | ML: {r['ml_accuracy']:5.1f}%")

    output = {
        "as_of": pd.Timestamp.now().isoformat(),
        "results": results
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\n[3] Saved: {OUT}")

if __name__ == "__main__":
    main()
