"""08_sarvrouter_timeline.py — Extract SarvRouter decisions + forward returns.

For each switch (when regime changes from prev non-unknown):
- date, index, price
- regime (current), prev_regime
- forward returns: 24h, 7d (168h), 30d (720h)
- correct on 24h: uptrend+positive=✅, downtrend+negative=✅, range+|x|<1%=✅

Output: frontend/public/data/sarvrouter-decisions.json

This is the data source for /research/sarvrouter-timeline page (future).
"""
from __future__ import annotations

import json
import sys
import tempfile
import time
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

DATA = Path("research/tsfresh/data/BTCUSDT_1h_full.csv")
OUT = Path("frontend/public/data/sarvrouter-decisions.json")

FORWARD_WINDOWS = [24, 168, 720]  # 24h, 7d, 30d
RANGE_THRESHOLD_PCT = 1.0  # |forward| < 1% = "correct" for range


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


def classify_correct(regime: str, fwd_ret: float | None) -> str | None:
    if fwd_ret is None:
        return None
    if regime == "uptrend":
        return "correct" if fwd_ret > 0 else "incorrect"
    if regime == "downtrend":
        return "correct" if fwd_ret < 0 else "incorrect"
    if regime == "range":
        return "correct" if abs(fwd_ret) < RANGE_THRESHOLD_PCT else "incorrect"
    return None


def main() -> None:
    print("=" * 60)
    print("  08_sarvrouter_timeline.py")
    print("=" * 60)

    print(f"\n[1] Loading {DATA}")
    candles = load_candles(DATA)
    print(f"    {len(candles)} candles")

    print(f"\n[2] Running SarvRouter backtest (~60s)")
    tmp = Path(tempfile.mkdtemp())
    router = SarvRouter(
        config=SarvRouterConfig(),
        start_bot=lambda s: None,
        stop_bot=lambda s: None,
        stop_all=lambda: None,
        store=SarvStore(base_dir=tmp),
        audit=AuditTrail(base_dir=tmp),
    )
    t0 = time.time()
    result = run_sarv_backtest(router, "timeline", candles)
    print(f"    done in {time.time()-t0:.1f}s")
    print(f"    total_ticks: {result['total_ticks']}")
    print(f"    switches (raw): {result['switches']}")

    regime_seq = result["regime_sequence"]

    # Find switch points (when regime changes from prev non-unknown)
    switches = []
    prev = None
    for i, r in enumerate(regime_seq):
        if r in ("uptrend", "downtrend", "range"):
            if prev is not None and r != prev:
                entry = {
                    "index": i,
                    "date": pd.Timestamp(candles[i].time, unit="s").isoformat(),
                    "price": float(candles[i].close),
                    "regime": r,
                    "prev_regime": prev,
                }
                for w in FORWARD_WINDOWS:
                    entry[f"forward_{w}h_pct"] = forward_return(candles, i, w)
                entry["correct_24h"] = classify_correct(r, entry["forward_24h_pct"])
                switches.append(entry)
            prev = r

    print(f"    switches (non-unknown transitions): {len(switches)}")

    # Per-regime accuracy (based on 24h)
    stats = {}
    for regime in ("uptrend", "downtrend", "range"):
        regime_switches = [s for s in switches if s["regime"] == regime]
        total = len(regime_switches)
        correct = sum(1 for s in regime_switches if s["correct_24h"] == "correct")
        incorrect = total - correct
        stats[regime] = {
            "total": total,
            "correct_24h": correct,
            "incorrect_24h": incorrect,
            "accuracy_pct": round(correct / total * 100, 1) if total > 0 else 0.0,
        }

    print(f"\n[3] Per-regime accuracy (24h forward):")
    for regime, s in stats.items():
        print(f"    {regime:12s}: {s['accuracy_pct']:5.1f}%  ({s['correct_24h']}/{s['total']})")

    overall_total = sum(s["total"] for s in stats.values())
    overall_correct = sum(s["correct_24h"] for s in stats.values())
    overall_acc = round(overall_correct / overall_total * 100, 1) if overall_total > 0 else 0
    print(f"    {'overall':12s}: {overall_acc:5.1f}%  ({overall_correct}/{overall_total})")

    # Output JSON
    output = {
        "as_of": pd.Timestamp.now().isoformat(),
        "data_source": "BTCUSDT (Binance, 5.8yr proxy)",
        "note": "Not BTCMN (Wallex). Verify on Wallex before Live.",
        "total_candles": len(candles),
        "first_date": pd.Timestamp(candles[0].time, unit="s").isoformat(),
        "last_date": pd.Timestamp(candles[-1].time, unit="s").isoformat(),
        "total_switches": len(switches),
        "forward_windows_hours": FORWARD_WINDOWS,
        "range_threshold_pct": RANGE_THRESHOLD_PCT,
        "overall_accuracy_24h": {"total": overall_total, "correct": overall_correct, "accuracy_pct": overall_acc},
        "stats": stats,
        "switches": switches,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    size_kb = round(OUT.stat().st_size / 1024, 1)
    print(f"\n[4] Saved: {OUT} ({size_kb} KB, {len(switches)} decisions)")
    print("\n✅ DONE")


if __name__ == "__main__":
    main()
