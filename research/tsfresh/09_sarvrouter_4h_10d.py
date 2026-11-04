"""09_sarvrouter_4h_10d.py — SarvRouter on 4h candles, 10d forward.

Rationale (Hosein 2026-11-04): 1h/24h is inherently noisy.
Test on 4h candles (4x less noise) with 10d forward (60 x 4h candles).
If regime detection works at all, it should show higher accuracy here.

Output: frontend/public/data/sarvrouter-4h-10d.json
Also saves decisions for potential UI.
"""
from __future__ import annotations

import json
import sys
import tempfile
import time
from dataclasses import replace
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, "backend")

import pandas as pd
from app.domain.entities.candle import Candle
from app.services.bots.sarv_router.bot import SarvRouter
from app.services.bots.sarv_router.config import SarvRouterConfig
from app.services.bots.sarv_router.store import SarvStore
from app.services.bots.sarv_router.audit import AuditTrail
from app.services.bots.sarv_router.backtest_adapter import run_sarv_backtest
from app.services.bots.sarv_router.resample import resample_4h

DATA = Path("research/tsfresh/data/BTCUSDT_1h_full.csv")
OUT = Path("frontend/public/data/sarvrouter-4h-10d.json")

# 4h bars: 10 days = 60 bars
FORWARD_BARS = [6, 42, 60]  # 1d, 7d, 10d (in 4h bars)
RANGE_THRESHOLD_PCT = 3.0  # for 10d, |x|<3% = "still range"


def load_candles(csv_path: Path) -> list[Candle]:
    df = pd.read_csv(csv_path)
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


def forward_return(candles: list[Candle], i: int, window: int) -> float | None:
    if i + window >= len(candles):
        return None
    entry = float(candles[i].close)
    exit_ = float(candles[i + window].close)
    if entry <= 0:
        return None
    return round((exit_ / entry - 1) * 100, 3)


def classify_correct(regime: str, fwd_ret: float | None, threshold: float) -> str | None:
    if fwd_ret is None:
        return None
    if regime == "uptrend":
        return "correct" if fwd_ret > 0 else "incorrect"
    if regime == "downtrend":
        return "correct" if fwd_ret < 0 else "incorrect"
    if regime == "range":
        return "correct" if abs(fwd_ret) < threshold else "incorrect"
    return None


def run_test(candles_4h: list[Candle], stability: int, label: str) -> dict:
    print(f"\n--- Test: {label} (stability={stability}) ---")
    cfg = replace(
        SarvRouterConfig(),
        enable_multi_tf=False,      # we ARE 4h
        stability_window=stability,
        cooldown_candles=3,         # 12h on 4h
        warmup_candles=30,          # 30 4h bars = 5 days
    )

    tmp = Path(tempfile.mkdtemp())
    router = SarvRouter(
        config=cfg,
        start_bot=lambda s: None,
        stop_bot=lambda s: None,
        stop_all=lambda: None,
        store=SarvStore(base_dir=tmp),
        audit=AuditTrail(base_dir=tmp),
    )
    t0 = time.time()
    result = run_sarv_backtest(router, "4h-test", candles_4h)
    print(f"  done in {time.time()-t0:.1f}s")
    print(f"  total_ticks: {result['total_ticks']}")
    print(f"  raw switches: {result['switches']}")

    regime_seq = result["regime_sequence"]

    # Find transitions (regime changes)
    switches = []
    prev = None
    for i, r in enumerate(regime_seq):
        if r in ("uptrend", "downtrend", "range"):
            if prev is not None and r != prev:
                entry = {
                    "index": i,
                    "date": pd.Timestamp(candles_4h[i].time, unit="s").isoformat(),
                    "price": float(candles_4h[i].close),
                    "regime": r,
                    "prev_regime": prev,
                }
                for w_bars in FORWARD_BARS:
                    days = w_bars * 4 // 24
                    entry[f"forward_{days}d_pct"] = forward_return(candles_4h, i, w_bars)
                # correct at 10d
                entry["correct_10d"] = classify_correct(r, entry["forward_10d_pct"], RANGE_THRESHOLD_PCT)
                entry["correct_7d"] = classify_correct(r, entry["forward_7d_pct"], RANGE_THRESHOLD_PCT)
                entry["correct_1d"] = classify_correct(r, entry["forward_1d_pct"], 1.0)
                switches.append(entry)
            prev = r

    print(f"  transitions: {len(switches)}")

    # Accuracy per regime at 10d
    stats_10d = {}
    for regime in ("uptrend", "downtrend", "range"):
        rs = [s for s in switches if s["regime"] == regime and s["correct_10d"] is not None]
        total = len(rs)
        correct = sum(1 for s in rs if s["correct_10d"] == "correct")
        stats_10d[regime] = {
            "total": total,
            "correct": correct,
            "accuracy_pct": round(correct / total * 100, 1) if total > 0 else 0.0,
        }

    overall_total = sum(s["total"] for s in stats_10d.values())
    overall_correct = sum(s["correct"] for s in stats_10d.values())
    overall_acc = round(overall_correct / overall_total * 100, 1) if overall_total > 0 else 0

    print(f"  --- Accuracy at 10d forward ---")
    for regime, s in stats_10d.items():
        print(f"    {regime:10s}: {s['accuracy_pct']:5.1f}%  ({s['correct']}/{s['total']})")
    print(f"    {'overall':10s}: {overall_acc:5.1f}%  ({overall_correct}/{overall_total})")

    return {
        "label": label,
        "stability": stability,
        "total_candles": len(candles_4h),
        "total_ticks": result["total_ticks"],
        "raw_switches": result["switches"],
        "transitions": len(switches),
        "stats_10d": stats_10d,
        "overall_accuracy_10d_pct": overall_acc,
        "overall_correct": overall_correct,
        "overall_total": overall_total,
        "switches": switches,
    }


def main() -> None:
    print("=" * 60)
    print("  09_sarvrouter_4h_10d.py")
    print("=" * 60)

    print(f"\n[1] Loading 1h data from {DATA}")
    candles_1h = load_candles(DATA)
    print(f"    {len(candles_1h)} 1h candles")

    print(f"\n[2] Resampling 1h → 4h")
    candles_4h = resample_4h(candles_1h)
    print(f"    {len(candles_4h)} 4h candles")
    print(f"    first: {pd.Timestamp(candles_4h[0].time, unit='s')}")
    print(f"    last:  {pd.Timestamp(candles_4h[-1].time, unit='s')}")

    # Test 3 stability windows
    tests = [
        (36, "default (36 bars = 6d)"),
        (12, "shorter (12 bars = 2d)"),
        (6,  "shortest (6 bars = 1d)"),
    ]

    results = []
    for stab, label in tests:
        r = run_test(candles_4h, stab, label)
        results.append(r)

    # Summary
    print(f"\n{'=' * 60}")
    print("  SUMMARY — 4h / 10d forward")
    print(f"{'=' * 60}")
    print(f"{'Label':30s} | {'Overall':10s} | uptrend | downtrend | range")
    print(f"{'-' * 30}-+-{'-' * 10}-+-{'-' * 7}-+-{'-' * 9}-+-{'-' * 5}")
    for r in results:
        s = r["stats_10d"]
        print(
            f"{r['label']:30s} | {r['overall_accuracy_10d_pct']:5.1f}% "
            f"({r['overall_correct']:4d}/{r['overall_total']:4d}) | "
            f"{s['uptrend']['accuracy_pct']:5.1f}% | "
            f"{s['downtrend']['accuracy_pct']:5.1f}%   | "
            f"{s['range']['accuracy_pct']:5.1f}%"
        )

    # Pick best (highest overall accuracy)
    best = max(results, key=lambda x: x["overall_accuracy_10d_pct"])
    print(f"\n>>> BEST: {best['label']} → {best['overall_accuracy_10d_pct']}%")

    # Save all (for UI)
    output = {
        "as_of": pd.Timestamp.now().isoformat(),
        "data_source": "BTCUSDT (Binance) 1h resampled to 4h",
        "note": "Not BTCMN (Wallex). Verify on Wallex before Live.",
        "forward_bars_hours": [b * 4 for b in FORWARD_BARS],
        "range_threshold_pct": RANGE_THRESHOLD_PCT,
        "tests": results,
        "best_test_label": best["label"],
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    size_mb = round(OUT.stat().st_size / 1024 / 1024, 2)
    print(f"\n[4] Saved: {OUT} ({size_mb} MB)")
    print("\n✅ DONE")


if __name__ == "__main__":
    main()
