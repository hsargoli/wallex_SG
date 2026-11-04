"""Grid search Nooaah params on BTCUSDT proxy (5.8yr).

Objective: find (sl_atr, tp_atr, min_conf) that maximize PF
subject to: WR >= 40%, trades >= 30.

Success (AP-57): PF > 1.0.
"""
from __future__ import annotations

import sys
import tempfile
import time
from dataclasses import replace
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, "backend")

import pandas as pd
from app.domain.entities.candle import Candle
from app.services.bots.nooaah.backtest import run_nooaah_backtest
from app.services.bots.nooaah.config import NooaahConfig

DATA = Path("research/tsfresh/data/BTCUSDT_1h_full.csv")
LIMIT = 10000  # 5 months — enough for grid search

# grid
SL_GRID = [1.0, 1.5, 2.0]
TP_GRID = [2.0, 3.0, 4.0]
CONF_GRID = [75, 85, 95]


def load_candles(csv_path: Path, limit: int | None = None) -> list[Candle]:
    df = pd.read_csv(csv_path)
    if limit:
        df = df.head(limit)
    times = df["datetime"].apply(lambda x: int(pd.Timestamp(x).timestamp())).values
    return [
        Candle(
            time=int(times[i]),
            open=Decimal(str(r["open"])),
            high=Decimal(str(r["high"])),
            low=Decimal(str(r["low"])),
            close=Decimal(str(r["close"])),
            volume=Decimal(str(r["volume"])),
        )
        for i, r in df.iterrows()
    ]


def evaluate(candles: list[Candle], sl: float, tp: float, conf: int) -> dict:
    """Run backtest with given params, return metrics."""
    cfg = replace(NooaahConfig(), sl_atr_mult=sl, tp_atr_mult=tp, min_confidence=conf)
    try:
        result = run_nooaah_backtest(
            candles_by_symbol={"BTCUSDT": candles},
            config=cfg,
            start_idx=200,
        )
        if not result.trades:
            return {"pf": 0, "wr": 0, "n": 0, "avg": 0, "max_dd": 0}
        rets = [t.return_pct for t in result.trades]
        wins = [r for r in rets if r > 0]
        losses = [r for r in rets if r <= 0]
        wr = len(wins) / len(rets)
        if losses:
            pf = sum(wins) / abs(sum(losses)) if sum(losses) != 0 else float("inf")
        else:
            pf = float("inf")
        # equity curve for max DD
        eq = [1.0]
        for r in rets:
            eq.append(eq[-1] * (1 + r / 100))
        peak = max(eq)
        max_dd = (min(eq[i] / peak for i in range(len(eq))) - 1) * 100
        return {
            "pf": round(pf, 3) if pf != float("inf") else "inf",
            "wr": round(wr * 100, 1),
            "n": len(rets),
            "avg": round(sum(rets) / len(rets), 3),
            "max_dd": round(max_dd, 1),
        }
    except Exception as e:
        return {"pf": 0, "wr": 0, "n": 0, "avg": 0, "max_dd": 0, "error": str(e)}


def main() -> None:
    print("=" * 70)
    print(f"  Grid Search Nooaah — BTCUSDT proxy ({LIMIT} candles)")
    print("=" * 70)

    print(f"\n[1] Loading data...")
    candles = load_candles(DATA, LIMIT)
    print(f"    {len(candles)} candles")

    print(f"\n[2] Grid: sl={SL_GRID} × tp={TP_GRID} × conf={CONF_GRID}")
    print(f"    = {len(SL_GRID) * len(TP_GRID) * len(CONF_GRID)} combinations")

    results = []
    t0 = time.time()
    for sl in SL_GRID:
        for tp in TP_GRID:
            for conf in CONF_GRID:
                m = evaluate(candles, sl, tp, conf)
                results.append({
                    "sl": sl, "tp": tp, "conf": conf, **m
                })
                pf = m["pf"]
                print(
                    f"    sl={sl} tp={tp} conf={conf} → "
                    f"PF={pf} WR={m['wr']}% n={m['n']} DD={m['max_dd']}%",
                    flush=True,
                )
    elapsed = time.time() - t0
    print(f"\n    Total time: {elapsed:.1f}s")

    # Sort by PF (only those passing WR>=40% and n>=30)
    print(f"\n[3] Best 5 combinations (WR>=40%, n>=30):")
    valid = [r for r in results if r["wr"] >= 40 and r["n"] >= 30]
    valid.sort(key=lambda x: (x["pf"] if x["pf"] != "inf" else 999, -x["max_dd"]), reverse=True)
    for i, r in enumerate(valid[:5]):
        print(f"    {i+1}. sl={r['sl']} tp={r['tp']} conf={r['conf']} → PF={r['pf']} WR={r['wr']}% n={r['n']} DD={r['max_dd']}%")

    if not valid:
        print(f"    ⚠️ No combination passed WR>=40% and n>=30.")
        # best by PF anyway
        all_sorted = sorted(results, key=lambda x: (x["pf"] if x["pf"] != "inf" else 999), reverse=True)
        print(f"\n[4] Best by PF (any WR):")
        for i, r in enumerate(all_sorted[:5]):
            print(f"    {i+1}. sl={r['sl']} tp={r['tp']} conf={r['conf']} → PF={r['pf']} WR={r['wr']}% n={r['n']} DD={r['max_dd']}%")

    print(f"\n✅ DONE")

    if valid:
        best = valid[0]
        print(f"\n>>> NEXT: verify on full 51K with params: --sl {best['sl']} --tp {best['tp']} --conf {best['conf']}")


if __name__ == "__main__":
    main()
