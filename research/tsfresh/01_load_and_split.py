"""01_load_and_split.py — Load BTCUSDT 1h candles, normalize timestamps, 3-way split.

Input:  backend/data/candles/historical/BTCUSDT_1h.csv
Output: research/tsfresh/data/{train,val,test}.csv
        research/tsfresh/data/split_metadata.json

Constraints:
- No features, no model (only load + split + save + gap report)
- Mixed timestamp normalization (10-digit sec, 13-digit ms → sec)
- Time-based split (no shuffle)
- Gap report: total > 1h, TOP 5 largest
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

INPUT = Path("backend/data/candles/historical/BTCUSDT_1h.csv")
OUT_DIR = Path("research/tsfresh/data")

TRAIN_END = pd.Timestamp("2024-06-30 23:59:59")
VAL_END = pd.Timestamp("2025-06-30 23:59:59")

MS_THRESHOLD = 10**12


def normalize_timestamp_to_seconds(series: pd.Series) -> pd.Series:
    """Mixed 10-digit (sec) / 13-digit (ms) → seconds."""
    return series.apply(lambda x: x / 1000 if x > MS_THRESHOLD else x)


def gap_report(df: pd.DataFrame, label: str) -> dict:
    """Gap statistics: total > 1h, total > 24h, TOP 5 largest."""
    diffs = df["datetime"].diff().dt.total_seconds()
    gap_indices = diffs[diffs > 3600].index.tolist()

    report = {
        "label": label,
        "total_gaps_gt_1h": len(gap_indices),
        "total_gaps_gt_24h": int((diffs > 86400).sum()),
        "top5": [],
    }

    gap_info = []
    for idx in gap_indices:
        gap_info.append({
            "from": str(df.loc[idx - 1, "datetime"]),
            "to": str(df.loc[idx, "datetime"]),
            "duration_hours": round(diffs.loc[idx] / 3600, 2),
        })
    gap_info.sort(key=lambda x: x["duration_hours"], reverse=True)
    report["top5"] = gap_info[:5]
    return report


def expected_hours(start: pd.Timestamp, end: pd.Timestamp) -> int:
    return int((end - start).total_seconds() / 3600) + 1


def split_stats(df: pd.DataFrame, label: str) -> dict:
    exp = expected_hours(df["datetime"].min(), df["datetime"].max())
    return {
        "label": label,
        "rows": int(len(df)),
        "expected_hours": int(exp),
        "coverage_pct": round(100 * len(df) / exp, 2) if exp > 0 else 0,
        "first": str(df["datetime"].min()),
        "last": str(df["datetime"].max()),
        "duration_days": int((df["datetime"].max() - df["datetime"].min()).total_seconds() / 86400),
    }


def main() -> None:
    print("=" * 60)
    print("  01_load_and_split.py — BTCUSDT 1h")
    print("=" * 60)

    print(f"\n[1] Reading: {INPUT}")
    if not INPUT.exists():
        raise SystemExit(f"❌ Input not found: {INPUT}")
    df = pd.read_csv(INPUT)
    print(f"    rows: {len(df)}")
    print(f"    columns: {list(df.columns)}")

    print(f"\n[2] Normalizing timestamp (ms→s where > {MS_THRESHOLD})")
    df["open_time_sec"] = normalize_timestamp_to_seconds(df["open_time"])
    df["datetime"] = pd.to_datetime(df["open_time_sec"], unit="s")
    print(f"    first: {df['datetime'].min()}")
    print(f"    last:  {df['datetime'].max()}")

    print("\n[3] Sorting by datetime")
    df = df.sort_values("datetime").reset_index(drop=True)
    print(f"    OK ({len(df)} rows)")

    print("\n[4] Gap report (whole dataset)")
    full_gap = gap_report(df, "ALL")
    print(f"    gaps > 1h:  {full_gap['total_gaps_gt_1h']}")
    print(f"    gaps > 24h: {full_gap['total_gaps_gt_24h']}")
    print("    TOP 5 largest gaps:")
    for i, g in enumerate(full_gap["top5"], 1):
        print(f"      {i}. {g['from']} → {g['to']}  ({g['duration_hours']}h)")

    print("\n[5] 3-way split (train/val/test)")
    train = df[df["datetime"] <= TRAIN_END].copy()
    val = df[(df["datetime"] > TRAIN_END) & (df["datetime"] <= VAL_END)].copy()
    test = df[df["datetime"] > VAL_END].copy()
    print(f"    TRAIN: {len(train)} rows (<= {TRAIN_END})")
    print(f"    VAL:   {len(val)} rows")
    print(f"    TEST:  {len(test)} rows")

    print("\n[6] Stats per split")
    train_stats = split_stats(train, "TRAIN")
    val_stats = split_stats(val, "VAL")
    test_stats = split_stats(test, "TEST")
    for s in (train_stats, val_stats, test_stats):
        print(f"    {s['label']:6s}: {s['rows']:5d} rows | "
              f"coverage {s['coverage_pct']:5.1f}% | "
              f"{s['first']} → {s['last']} | {s['duration_days']}d")

    print(f"\n[7] Saving to {OUT_DIR}/")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    cols = ["datetime", "open", "high", "low", "close", "volume"]
    train[cols].to_csv(OUT_DIR / "train.csv", index=False)
    val[cols].to_csv(OUT_DIR / "val.csv", index=False)
    test[cols].to_csv(OUT_DIR / "test.csv", index=False)
    print(f"    train.csv: {len(train)} rows")
    print(f"    val.csv:   {len(val)} rows")
    print(f"    test.csv:  {len(test)} rows")

    print("\n[8] Writing metadata")
    metadata = {
        "input": str(INPUT),
        "output_dir": str(OUT_DIR),
        "threshold_ms": MS_THRESHOLD,
        "split_boundaries": {"train_end": str(TRAIN_END), "val_end": str(VAL_END)},
        "total_rows": int(len(df)),
        "stats": {"train": train_stats, "val": val_stats, "test": test_stats},
        "gap_report": full_gap,
    }
    with open(OUT_DIR / "split_metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False, default=str)
    print("    split_metadata.json written")

    print("\n" + "=" * 60)
    print("  ✅ DONE")
    print("=" * 60)


if __name__ == "__main__":
    main()
