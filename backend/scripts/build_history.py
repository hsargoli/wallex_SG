"""Build historical window archive for sarv_tiger analyzer.

Pipeline:
    CSV (1h, mixed ts) → load_candles_csv (normalize_ts)
                      → resample_ohlc (4h)
                      → build_windows (features + outcomes)
                      → JSONL

Usage:
    # Smoke (last 500 1h candles)
    python scripts/build_history.py --limit 500

    # Full
    python scripts/build_history.py

    # Full + custom paths
    python scripts/build_history.py --input path/to.csv --output path/to.jsonl

Output format: one JSON object per line = one HistoricalWindow.to_dict().
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

# Make `app` importable when run from backend/ dir
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.bots.sarv_tiger.analyzer.csv_loader import load_candles_csv
from app.services.bots.sarv_tiger.analyzer.history import build_windows
from app.services.bots.sarv_tiger.analyzer.resample import resample_ohlc


DEFAULT_INPUT = Path("data/candles/historical/BTCUSDT_1h.csv")
DEFAULT_OUTPUT = Path("data/sarv_tiger/history.jsonl")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build sarv_tiger history archive")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--limit", type=int, default=0,
                        help="Take last N 1h candles (0 = all)")
    parser.add_argument("--window", type=int, default=20)
    parser.add_argument("--factor", type=int, default=4)
    args = parser.parse_args()

    print(f"input:  {args.input}")
    print(f"output: {args.output}")
    print(f"limit:  {args.limit if args.limit > 0 else 'full'}")
    print(f"window: {args.window}, factor: {args.factor}")
    print()

    if not args.input.exists():
        print(f"ERROR: input not found: {args.input}")
        return 1

    # --- Load ---
    t0 = time.time()
    candles_1h = load_candles_csv(args.input)
    print(f"[1/3] loaded 1h: {len(candles_1h)} candles ({time.time() - t0:.1f}s)")

    if args.limit > 0 and len(candles_1h) > args.limit:
        candles_1h = candles_1h[-args.limit:]
        print(f"      limited to last {len(candles_1h)} 1h candles")

    # Sanity: all timestamps must be seconds now
    bad_ts = sum(1 for c in candles_1h if int(c.time) >= 10_000_000_000)
    if bad_ts:
        print(f"ERROR: {bad_ts} timestamps still in ms (normalize_ts bug?)")
        return 1

    # --- Resample 1h -> 4h ---
    t0 = time.time()
    candles_4h = resample_ohlc(candles_1h, factor=args.factor)
    print(f"[2/3] resampled to 4h: {len(candles_4h)} candles ({time.time() - t0:.1f}s)")

    # --- Build windows ---
    t0 = time.time()
    windows = build_windows(candles_4h, window=args.window)
    print(f"[3/3] built windows: {len(windows)} ({time.time() - t0:.1f}s)")

    if not windows:
        print("ERROR: 0 windows (insufficient data)")
        return 1

    # --- Stats ---
    n = len(windows)
    p_up_24h = sum(1 for w in windows if w.outcome_24h > 0) / n
    p_up_72h = sum(1 for w in windows if w.outcome_72h > 0) / n
    p_hit_tp = sum(1 for w in windows if w.hit_tp_24h) / n
    p_hit_sl = sum(1 for w in windows if w.hit_sl_24h) / n
    avg_24h = sum(w.outcome_24h for w in windows) / n

    print()
    print("=== stats ===")
    print(f"  count:    {n}")
    print(f"  ts range: {windows[0].window_start_ts} .. {windows[-1].window_end_ts}")
    print(f"  p_up_24h: {p_up_24h:.2%}")
    print(f"  p_up_72h: {p_up_72h:.2%}")
    print(f"  p_hit_tp: {p_hit_tp:.2%}   (8.0 ATR up within 24h)")
    print(f"  p_hit_sl: {p_hit_sl:.2%}   (1.2 ATR down within 24h)")
    print(f"  avg_ret_24h: {avg_24h:+.4%}")

    # --- Save JSONL ---
    args.output.parent.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    with args.output.open("w") as f:
        for w in windows:
            f.write(json.dumps(w.to_dict()) + "\n")
    size_mb = args.output.stat().st_size / (1024 * 1024)
    print()
    print(f"saved: {args.output} ({size_mb:.2f} MB, {time.time() - t0:.1f}s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
