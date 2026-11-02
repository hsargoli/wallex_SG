"""02b_real_baseline.py — Real baselines: B&H + MA Crossover Long-Short.

Per AP-57 (define success before code):
- B&H: 1 trade, hold full split. Report: return, max_dd, duration.
- MA(50/200) Crossover: long when EMA50 > EMA200, short otherwise.
  Position changes at each crossover. Report: PF, WR, DD, N trades.

Cost model (Primer lesson 33):
- fee=0.2%/side × 2 = 0.4%
- slippage=0.1%/side × 2 = 0.2%
- spread=0.05% total
- round-trip cost ≈ 0.65%

NO tsfresh, NO ML here — pure strategy baselines.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

DATA_DIR = Path("research/tsfresh/data")
OUT_DIR = Path("research/tsfresh")

FEE = 0.002
SLIPPAGE = 0.001
SPREAD = 0.0005
ROUND_TRIP_COST = 2 * FEE + 2 * SLIPPAGE + SPREAD  # 0.0065 = 0.65%

FAST = 50
SLOW = 200

TRAIN_END = "2024-06-30 23:59:59"
VAL_END = "2025-06-30 23:59:59"


# ─── Helpers ─────────────────────────────────────────────────────────
def compute_emas(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["ema_fast"] = df["close"].ewm(span=FAST, adjust=False).mean()
    df["ema_slow"] = df["close"].ewm(span=SLOW, adjust=False).mean()
    df["signal"] = np.where(df["ema_fast"] > df["ema_slow"], 1, -1)
    return df


def dd_from_equity(eq: np.ndarray) -> float:
    peak = np.maximum.accumulate(eq)
    dd = (eq - peak) / peak
    return float(dd.min())


# ─── B&H ─────────────────────────────────────────────────────────────
def backtest_bnh(df: pd.DataFrame) -> dict:
    if len(df) < 2:
        return {"error": "too few rows"}

    entry = float(df["close"].iloc[0])
    exit_ = float(df["close"].iloc[-1])
    gross = exit_ / entry - 1
    net = gross - ROUND_TRIP_COST

    eq = (df["close"] / entry).values
    max_dd = dd_from_equity(eq)

    return {
        "n_trades": 1,
        "entry_price": entry,
        "exit_price": exit_,
        "gross_return": round(gross, 6),
        "net_return": round(net, 6),
        "max_dd": round(max_dd, 6),
        "duration_hours": int(len(df)),
        "first": str(df["datetime"].iloc[0]),
        "last": str(df["datetime"].iloc[-1]),
    }


# ─── MA Crossover (Long-Short) ───────────────────────────────────────
def backtest_ma(df: pd.DataFrame) -> dict:
    """Position = signal from EMA50 vs EMA200. Long when fast>slow, short otherwise."""
    if len(df) < 2:
        return {"error": "too few rows"}

    closes = df["close"].values
    signals = df["signal"].values
    times = df["datetime"].values

    trades = []
    position = 0
    entry_price = None
    entry_time = None

    for i in range(len(df)):
        sig = int(signals[i])
        price = float(closes[i])
        t = times[i]

        if sig != position:
            # close existing
            if position != 0 and entry_price is not None:
                if position == 1:
                    gross = (price - entry_price) / entry_price
                else:
                    gross = (entry_price - price) / entry_price
                net = gross - ROUND_TRIP_COST
                trades.append({
                    "direction": "long" if position == 1 else "short",
                    "entry_time": str(entry_time),
                    "exit_time": str(t),
                    "entry_price": entry_price,
                    "exit_price": price,
                    "gross_return": gross,
                    "net_return": net,
                })
            # open new
            position = sig
            entry_price = price
            entry_time = t

    # close at end if open
    if position != 0 and entry_price is not None:
        price = float(closes[-1])
        t = times[-1]
        if position == 1:
            gross = (price - entry_price) / entry_price
        else:
            gross = (entry_price - price) / entry_price
        net = gross - ROUND_TRIP_COST
        trades.append({
            "direction": "long" if position == 1 else "short",
            "entry_time": str(entry_time),
            "exit_time": str(t),
            "entry_price": entry_price,
            "exit_price": price,
            "gross_return": gross,
            "net_return": net,
        })

    if not trades:
        return {"n_trades": 0, "error": "no trades generated"}

    rets = np.array([t["net_return"] for t in trades])
    wins = rets[rets > 0]
    losses = rets[rets <= 0]

    pf = float(wins.sum() / abs(losses.sum())) if losses.sum() != 0 else float("inf")
    wr = float(len(wins) / len(rets))
    eq = np.cumprod(1 + rets)
    max_dd = dd_from_equity(eq)

    n_long = sum(1 for t in trades if t["direction"] == "long")
    n_short = sum(1 for t in trades if t["direction"] == "short")

    return {
        "n_trades": int(len(trades)),
        "n_long": n_long,
        "n_short": n_short,
        "win_rate": round(wr, 4),
        "profit_factor": round(pf, 4) if pf != float("inf") else "inf",
        "total_return": round(float(eq[-1] - 1), 4),
        "max_dd": round(max_dd, 4),
        "avg_return_per_trade": round(float(rets.mean()), 6),
    }


# ─── Run one split ───────────────────────────────────────────────────
def run_split(df: pd.DataFrame, label: str) -> dict:
    print(f"\n[{label}] {len(df)} rows | {df['datetime'].iloc[0]} → {df['datetime'].iloc[-1]}")
    bnh = backtest_bnh(df)
    ma = backtest_ma(df)

    print(f"  B&H:  gross={bnh.get('gross_return')}, net={bnh.get('net_return')}, "
          f"maxDD={bnh.get('max_dd')}")
    if "error" not in ma:
        print(f"  MA:   n={ma['n_trades']} (L={ma['n_long']}/S={ma['n_short']}), "
              f"WR={ma['win_rate']}, PF={ma['profit_factor']}, "
              f"ret={ma['total_return']}, DD={ma['max_dd']}")
    else:
        print(f"  MA:   {ma}")

    return {"bnh": bnh, "ma": ma}


# ─── Run one timeframe ───────────────────────────────────────────────
def run_tf(df: pd.DataFrame, tf_name: str) -> dict:
    print(f"\n{'=' * 60}")
    print(f"  {tf_name}")
    print(f"{'=' * 60}")

    df = compute_emas(df)
    val = df[(df["datetime"] > TRAIN_END) & (df["datetime"] <= VAL_END)].reset_index(drop=True)
    test = df[df["datetime"] > VAL_END].reset_index(drop=True)

    return {
        "timeframe": tf_name,
        "val": run_split(val, f"{tf_name} VAL"),
        "test": run_split(test, f"{tf_name} TEST"),
    }


# ─── Main ────────────────────────────────────────────────────────────
def main() -> None:
    print("=" * 60)
    print("  02b_real_baseline.py — B&H + MA(50/200) L/S")
    print("=" * 60)
    print(f"Cost: fee={FEE*100:.2f}%/side, slip={SLIPPAGE*100:.1f}%/side, "
          f"spread={SPREAD*100:.2f}% → round-trip ≈ {ROUND_TRIP_COST*100:.2f}%")
    print(f"EMA: fast={FAST}, slow={SLOW}")

    # Load
    print(f"\nLoading: {DATA_DIR}/BTCUSDT_1h_full.csv")
    df_1h = pd.read_csv(DATA_DIR / "BTCUSDT_1h_full.csv")
    df_1h["datetime"] = pd.to_datetime(df_1h["datetime"])
    print(f"  {len(df_1h)} rows")

    # 1h
    result_1h = run_tf(df_1h.copy(), "1h")

    # 1D (resample)
    print(f"\nResampling 1h → 1D ...")
    df_1d = df_1h.set_index("datetime").resample("1D").agg({
        "open": "first", "high": "max", "low": "min",
        "close": "last", "volume": "sum",
    }).dropna().reset_index()
    print(f"  {len(df_1d)} daily candles")

    result_1D = run_tf(df_1d, "1D")

    # Summary
    print(f"\n{'=' * 60}")
    print("  SUMMARY")
    print(f"{'=' * 60}")
    print(f"{'TF':4s} | {'split':6s} | {'B&H ret':10s} | {'B&H DD':8s} | "
          f"{'MA PF':8s} | {'MA WR':7s} | {'MA DD':8s} | {'MA trades':9s}")
    best_pf = 0.0
    for r in (result_1h, result_1D):
        for split in ("val", "test"):
            bnh = r[split]["bnh"]
            ma = r[split]["ma"]
            pf_str = str(ma.get("profit_factor", "n/a"))
            try:
                if pf_str != "inf":
                    best_pf = max(best_pf, float(pf_str))
            except (ValueError, TypeError):
                pass
            print(f"{r['timeframe']:4s} | {split:6s} | "
                  f"{bnh.get('net_return', 'n/a'):>10} | "
                  f"{bnh.get('max_dd', 'n/a'):>8} | "
                  f"{pf_str:>8} | "
                  f"{ma.get('win_rate', 'n/a'):>7} | "
                  f"{ma.get('max_dd', 'n/a'):>8} | "
                  f"{ma.get('n_trades', 'n/a'):>9}")

    # Exit criteria barrier
    print(f"\n{'=' * 60}")
    print("  EXIT CRITERIA BARRIER (per AP-57)")
    print(f"{'=' * 60}")
    print(f"  Best baseline PF (val+test, both TF) = {best_pf}")
    print(f"  tsfresh must exceed: PF > 1.2 AND PF > {round(best_pf * 1.05, 4)}")
    print(f"  → effective threshold: PF > {max(1.2, round(best_pf * 1.05, 4))}")
    print(f"  Also: AUC > 0.55")

    # Save
    out = {
        "config": {
            "fee": FEE, "slippage": SLIPPAGE, "spread": SPREAD,
            "round_trip_cost": ROUND_TRIP_COST,
            "ema_fast": FAST, "ema_slow": SLOW,
        },
        "results_1h": result_1h,
        "results_1D": result_1D,
        "best_baseline_pf": best_pf,
        "tsfresh_threshold_pf": max(1.2, round(best_pf * 1.05, 4)),
    }
    out_path = OUT_DIR / "real_baseline_results.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False, default=str)
    print(f"\nSaved: {out_path}")
    print("\n✅ DONE")


if __name__ == "__main__":
    main()
