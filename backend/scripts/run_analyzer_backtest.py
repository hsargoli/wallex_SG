"""Run analyzer-only backtest — smoke / full / walk-forward / sensitivity.

Usage:
    # Smoke (last 3000 windows → faster)
    python scripts/run_analyzer_backtest.py --limit 3000

    # Full
    python scripts/run_analyzer_backtest.py

    # Only sensitivity (no walk-forward)
    python scripts/run_analyzer_backtest.py --sensitivity

Output: readable report to stdout. Numbers are the evidence for decision 5.5.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.bots.sarv_tiger.analyzer.backtest_analyzer_only import (
    run_backtest,
)
from app.services.bots.sarv_tiger.analyzer.csv_loader import load_candles_csv
from app.services.bots.sarv_tiger.analyzer.resample import resample_ohlc


HISTORY_PATH = Path("data/sarv_tiger/history.jsonl")
CANDLES_PATH = Path("data/candles/historical/BTCUSDT_1h.csv")


def _load_windows(path: Path) -> list[dict]:
    out = []
    with path.open("r") as f:
        for line in f:
            out.append(json.loads(line))
    return out


def _print_result(label: str, res, n_total: int) -> None:
    n = len(res.trades)
    print(f"  {label:14s} n={n:4d}/{n_total:<4d}  "
          f"PF={res.pf:6.2f}  WR={res.win_rate:6.1%}  "
          f"PnL={res.total_pnl:+7.2%}  DD={res.max_dd:6.2%}")


def _walk_forward(
    windows: list[dict], candles_4h, cfg, train_ratio: float, k: int,
) -> None:
    """Split test period into 3 sub-blocks and report each."""
    n = len(windows)
    train_n = int(n * train_ratio)
    test_n = n - train_n
    if test_n < 30:
        print("  (walk-forward skipped: test set too small)")
        return
    print(f"\n=== walk-forward (3 sub-blocks of test period) ===")
    block = test_n // 3
    train_windows = windows[:train_n]
    for i in range(3):
        start = train_n + i * block
        end = train_n + (i + 1) * block if i < 2 else n
        test_block = windows[start:end]
        combined = train_windows + test_block
        _, res = run_backtest(
            combined, candles_4h, cfg=cfg, train_ratio=train_n / len(combined),
            k=k,
        )
        _print_result(f"block {i + 1}", res, len(test_block))


def _sensitivity(
    windows: list[dict], candles_4h, cfg, train_ratio: float,
) -> None:
    print(f"\n=== sensitivity (K) ===")
    for k in (30, 50, 70):
        _, test = run_backtest(
            windows, candles_4h, cfg=cfg, train_ratio=train_ratio, k=k,
        )
        _print_result(f"K={k}", test, len(test[1:]) if False else len(windows))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0,
                    help="Use last N windows (0 = all)")
    ap.add_argument("--train-ratio", type=float, default=0.7)
    ap.add_argument("--k", type=int, default=50)
    ap.add_argument("--signal-mode", default="delta",
                    choices=["delta", "alpha", "gamma"])
    ap.add_argument("--sensitivity", action="store_true")
    ap.add_argument("--no-walkforward", action="store_true")
    ap.add_argument("--candles", type=Path, default=CANDLES_PATH)
    ap.add_argument("--history", type=Path, default=HISTORY_PATH)
    args = ap.parse_args()

    from app.services.bots.sarv_tiger.analyzer.analyzer_config import (
        AnalyzerConfig,
    )

    print(f"history: {args.history}")
    print(f"candles: {args.candles}")
    print(f"limit:   {args.limit if args.limit > 0 else 'full'}")
    print(f"k:       {args.k}, signal_mode: {args.signal_mode}")
    print(f"train:   {args.train_ratio:.0%}")
    print()

    # Load
    t0 = time.time()
    windows = _load_windows(args.history)
    if args.limit > 0:
        windows = windows[-args.limit:]
    print(f"[1/3] loaded {len(windows)} windows ({time.time() - t0:.1f}s)")

    t0 = time.time()
    c1h = load_candles_csv(args.candles)
    candles_4h = resample_ohlc(c1h, factor=4)
    print(f"[2/3] loaded {len(candles_4h)} 4h candles ({time.time() - t0:.1f}s)")

    cfg = AnalyzerConfig(signal_mode=args.signal_mode, k=args.k)

    t0 = time.time()
    train_res, test_res = run_backtest(
        windows, candles_4h, cfg=cfg, train_ratio=args.train_ratio, k=args.k,
    )
    print(f"[3/3] backtest done ({time.time() - t0:.1f}s)")

    print()
    print("=== main ===")
    _print_result("train", train_res, len(windows))
    _print_result("test", test_res, len(windows))

    if not args.no_walkforward:
        _walk_forward(windows, candles_4h, cfg, args.train_ratio, args.k)

    if args.sensitivity:
        _sensitivity(windows, candles_4h, cfg, args.train_ratio)

    # Baseline sanity: what would "always long" do?
    print(f"\n=== reference ===")
    print(f"  baseline p_up_168h across all windows: "
          f"{sum(1 for w in windows if w['outcome_168h'] > 0) / len(windows):.1%}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
