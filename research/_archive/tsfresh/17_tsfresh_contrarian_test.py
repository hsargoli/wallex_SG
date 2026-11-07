"""17_tsfresh_contrarian_test.py — H5/H6 Contrarian Hypothesis Tests.

Pre-registered (see ADR-0036):
    H5 (--mode short):    all GREEN → SHORT
    H6 (--mode long_red): all RED   → LONG

Context (long backtest, 15_tsfresh_trading_backtest.py):
    N=5,  24h: WR=33.0%, PF=0.58
    N=10, 24h: WR=26.0%, PF=0.42
    N=5,  72h: WR=33.1%, PF=0.58
    N=10, 72h: WR=31.6%, PF=0.55
    All below break-even WR ~44.2% (TP=4/SL=2/Fee=0.65).
    Key: stronger signal (N=10) was WORSE than N=5 for long.
    Hypothesis: signal is CONTRARIAN.

Design (isolate direction, keep everything else identical to 15):
    - Features: SAME as 15
    - Signal horizon: 24h (same)
    - Barriers: TP=4%, SL=2%, MaxHold=72h, Fee=0.65% (same)
    - Only difference: entry direction and signal color

Success criteria (AP-57, AP-58):
    trades >= 30 AND PF > 1.2 AND WR > 44.2% AND MaxDD > -20%

After H5/H6: ARCHIVE (AP-39).
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, "backend")

import numpy as np
import pandas as pd

DATA = Path("research/tsfresh/data/BTCUSDT_1h_full.csv")
OUT_SHORT = Path("frontend/public/data/tsfresh-backtest_H5_short.json")
OUT_LONG_RED = Path("frontend/public/data/tsfresh-backtest_H6_long_red.json")

WINDOW = 24
N_MATCHES = 10
TP_PCT = 4.0
SL_PCT = 2.0
MAX_HOLD = 72
FEE_PCT = 0.65

# net P&L per outcome (barrier hit)
WIN_NET = TP_PCT - FEE_PCT   # +3.35
LOSS_NET = SL_PCT + FEE_PCT  # -2.65
BREAK_EVEN_WR = LOSS_NET / (WIN_NET + LOSS_NET) * 100  # ~44.2%


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """Same features as 15 (19 features, 3 placeholders) — isolation."""
    df = df.copy()
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
    tr = pd.concat(
        [df["high"] - df["low"],
         (df["high"] - df["close"].shift()).abs(),
         (df["low"] - df["close"].shift()).abs()],
        axis=1,
    ).max(axis=1)
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
    out["close_position"] = (
        (df["close"] - df["low"].rolling(WINDOW).min())
        / (df["high"].rolling(WINDOW).max() - df["low"].rolling(WINDOW).min())
    )
    out["hh_ll_ratio"] = (
        (df["high"].rolling(WINDOW).max() - df["low"].rolling(WINDOW).min())
        / df["close"]
    )
    out["upper_wick_mean"] = 0.0
    out["lower_wick_mean"] = 0.0
    out["body_ratio_mean"] = 0.0
    return out


def run_backtest(mode: str, df: pd.DataFrame) -> dict:
    """mode='short': all GREEN → SHORT. mode='long_red': all RED → LONG."""
    assert mode in ("short", "long_red")
    is_short = mode == "short"

    feats = build_features(df)
    fwd_ret = (df["close"].shift(-24) / df["close"] - 1) * 100  # signal horizon: 24h
    feats = feats.replace([np.inf, -np.inf], np.nan)
    fwd_ret = fwd_ret.replace([np.inf, -np.inf], np.nan)
    valid = feats.dropna().index.intersection(fwd_ret.dropna().index)
    feats = feats.loc[valid]
    fwd_ret = fwd_ret.loc[valid]
    df2 = df.loc[valid]

    # pandas 2.x CoW: .values is read-only; use .to_numpy(copy=True)
    mu = feats.mean().to_numpy(dtype=float, copy=True)
    sigma = feats.std().to_numpy(dtype=float, copy=True)
    sigma[sigma == 0] = 1.0
    X = (feats.to_numpy(dtype=float) - mu) / sigma
    X_norm = np.linalg.norm(X, axis=1, keepdims=True)
    X_norm[X_norm == 0] = 1e-9
    X_unit = X / X_norm

    closes = df2["close"].values
    highs = df2["high"].values
    lows = df2["low"].values
    n = len(df2)

    trades = []
    rejections = {"not_match": 0}
    signal_count = 0
    in_position = False
    entry_idx = -1
    entry_price = 0.0

    t0 = time.time()
    for i in range(200, n):
        if in_position:
            # Barrier check at candle i (conservative: SL first if both hit)
            if is_short:
                sl_price = entry_price * (1 + SL_PCT / 100)
                tp_price = entry_price * (1 - TP_PCT / 100)
                if highs[i] >= sl_price:
                    trades.append({"entry": entry_idx, "exit": i, "ret": -LOSS_NET, "reason": "SL"})
                    in_position = False
                    continue
                elif lows[i] <= tp_price:
                    trades.append({"entry": entry_idx, "exit": i, "ret": WIN_NET, "reason": "TP"})
                    in_position = False
                    continue
            else:  # long_red (long direction)
                sl_price = entry_price * (1 - SL_PCT / 100)
                tp_price = entry_price * (1 + TP_PCT / 100)
                if lows[i] <= sl_price:
                    trades.append({"entry": entry_idx, "exit": i, "ret": -LOSS_NET, "reason": "SL"})
                    in_position = False
                    continue
                elif highs[i] >= tp_price:
                    trades.append({"entry": entry_idx, "exit": i, "ret": WIN_NET, "reason": "TP"})
                    in_position = False
                    continue
            # Timeout
            if i >= entry_idx + MAX_HOLD:
                exit_price = closes[i]
                if is_short:
                    ret = (1 - exit_price / entry_price) * 100 - FEE_PCT
                else:
                    ret = (exit_price / entry_price - 1) * 100 - FEE_PCT
                trades.append({"entry": entry_idx, "exit": i, "ret": ret, "reason": "Timeout"})
                in_position = False
            continue

        # Entry
        if i + MAX_HOLD >= n:
            break
        max_past = i - 24
        if max_past <= 0:
            continue
        sims = X_unit[i] @ X_unit[:max_past].T
        topN_idx = np.argsort(sims)[-N_MATCHES:]

        if is_short:
            signal = all(fwd_ret.iloc[idx] > 0 for idx in topN_idx)
        else:
            signal = all(fwd_ret.iloc[idx] < 0 for idx in topN_idx)

        if signal:
            signal_count += 1
            in_position = True
            entry_idx = i
            entry_price = closes[i]
        else:
            rejections["not_match"] += 1

        if i % 5000 == 0:
            print(f"    [progress] {i} ticks, {len(trades)} trades in {time.time()-t0:.1f}s")

    rets = np.array([t["ret"] for t in trades]) if trades else np.array([])
    if len(rets) > 0:
        wins = rets[rets > 0]
        losses = rets[rets <= 0]
        pf = wins.sum() / abs(losses.sum()) if losses.sum() != 0 else float("inf")
        wr = len(wins) / len(rets) * 100
        eq = [1.0]
        for r in rets:
            eq.append(eq[-1] * (1 + r / 100))
        peak = np.maximum.accumulate(eq)
        dd = (eq - peak) / peak
        max_dd = dd.min() * 100
        total_ret = (eq[-1] - 1) * 100
    else:
        pf = wr = max_dd = total_ret = 0.0

    return {
        "mode": mode,
        "params": {
            "window": WINDOW, "N": N_MATCHES, "TP": TP_PCT, "SL": SL_PCT,
            "MaxHold": MAX_HOLD, "Fee": FEE_PCT,
            "break_even_wr": round(BREAK_EVEN_WR, 1),
        },
        "stats": {
            "trades": len(trades),
            "win_rate": round(wr, 1),
            "profit_factor": round(pf, 2) if pf != float("inf") else "inf",
            "total_return": round(total_ret, 1),
            "max_dd": round(max_dd, 1),
            "TP": sum(1 for t in trades if t["reason"] == "TP"),
            "SL": sum(1 for t in trades if t["reason"] == "SL"),
            "Timeout": sum(1 for t in trades if t["reason"] == "Timeout"),
        },
        "rejections": {**rejections, "signal_count": signal_count},
        "trades": trades[-50:],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", required=True, choices=["short", "long_red"])
    args = parser.parse_args()

    print("=" * 60)
    print(f"  17_tsfresh_contrarian_test.py --mode {args.mode}")
    print("=" * 60)

    print(f"\n[1] Loading {DATA}")
    df = pd.read_csv(DATA)[["open", "high", "low", "close", "volume"]].copy()
    print(f"    {len(df)} candles")

    print(f"\n[2] Running backtest (mode={args.mode}, N={N_MATCHES}, TP={TP_PCT}/SL={SL_PCT})")
    result = run_backtest(args.mode, df)

    print(f"\n[3] Results ({args.mode})")
    s = result["stats"]
    print(f"    Trades: {s['trades']}")
    print(f"    Win Rate: {s['win_rate']}% (break-even: {result['params']['break_even_wr']}%)")
    print(f"    Profit Factor: {s['profit_factor']}")
    print(f"    Total Return: {s['total_return']}%")
    print(f"    Max DD: {s['max_dd']}%")
    print(f"    TP/SL/Timeout: {s['TP']}/{s['SL']}/{s['Timeout']}")
    print(f"    Rejections: {result['rejections']}")

    out_path = OUT_SHORT if args.mode == "short" else OUT_LONG_RED
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2)
    print(f"\n[4] Saved: {out_path}")

    # Verdict
    success = (
        s["trades"] >= 30
        and isinstance(s["profit_factor"], (int, float))
        and s["profit_factor"] > 1.2
        and s["win_rate"] > result["params"]["break_even_wr"]
        and s["max_dd"] > -20
    )
    print(f"\n[5] VERDICT ({args.mode}): {'SUCCESS' if success else 'FAIL'}")
    print(f"    Criteria: trades>=30 ({s['trades']>=30}), PF>1.2 ({s['profit_factor'] if isinstance(s['profit_factor'], str) else s['profit_factor']>1.2}), WR>BE ({s['win_rate']}>{result['params']['break_even_wr']}), MaxDD>-20 ({s['max_dd']}>-20)")


if __name__ == "__main__":
    main()
