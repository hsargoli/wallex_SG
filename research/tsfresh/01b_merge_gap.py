"""01b_merge_gap.py — Merge 8 missing months (2021-07 → 2022-02) + re-split.

Reads:
- backend/data/candles/historical/BTCUSDT_1h.csv (main, mixed ts)
- backend/data/candles/zips/BTCUSDT/BTCUSDT-1h-{2021-07..2022-02}.zip (12-col, ms)

Writes:
- research/tsfresh/data/BTCUSDT_1h_full.csv
- research/tsfresh/data/{train,val,test}.csv  (overwrites 01's output)
- research/tsfresh/data/split_metadata_full.json
"""
from __future__ import annotations

import json
import zipfile
from pathlib import Path

import pandas as pd

MAIN = Path("backend/data/candles/historical/BTCUSDT_1h.csv")
ZIPS_DIR = Path("backend/data/candles/zips/BTCUSDT")
MONTHS = ["2021-07", "2021-08", "2021-09", "2021-10",
          "2021-11", "2021-12", "2022-01", "2022-02"]
OUT_DIR = Path("research/tsfresh/data")

TRAIN_END = pd.Timestamp("2024-06-30 23:59:59")
VAL_END = pd.Timestamp("2025-06-30 23:59:59")
MS = 10**12


def norm_ts(s: pd.Series) -> pd.Series:
    return s.apply(lambda x: x / 1000 if x > MS else x)


def load_main() -> pd.DataFrame:
    df = pd.read_csv(MAIN)
    df["open_time_sec"] = norm_ts(df["open_time"])
    return df[["open_time_sec", "open", "high", "low", "close", "volume"]].rename(
        columns={"open_time_sec": "open_time"})


def load_zips() -> pd.DataFrame:
    parts = []
    for month in MONTHS:
        zp = ZIPS_DIR / f"BTCUSDT-1h-{month}.zip"
        if not zp.exists():
            print(f"  ❌ {month}: missing")
            continue
        with zipfile.ZipFile(zp) as z:
            name = z.namelist()[0]
            with z.open(name) as f:
                d = pd.read_csv(f, header=None, names=[
                    "open_time", "open", "high", "low", "close", "volume",
                    "ct", "qv", "cnt", "tbb", "tbq", "ig",
                ])
        d = d[["open_time", "open", "high", "low", "close", "volume"]]
        d["open_time"] = d["open_time"] / 1000.0
        parts.append(d)
        print(f"  {month}: {len(d)} rows")
    return pd.concat(parts, ignore_index=True)


def gap_report(df: pd.DataFrame) -> dict:
    diffs = df["datetime"].diff().dt.total_seconds()
    gaps = diffs[diffs > 3600]
    top = []
    for idx in gaps.index:
        top.append({
            "from": str(df.loc[idx - 1, "datetime"]),
            "to": str(df.loc[idx, "datetime"]),
            "hours": round(gaps.loc[idx] / 3600, 2),
        })
    top.sort(key=lambda x: x["hours"], reverse=True)
    return {
        "count_gt_1h": int(len(gaps)),
        "count_gt_24h": int((diffs > 86400).sum()),
        "top5": top[:5],
    }


def split_stats(df: pd.DataFrame, label: str) -> dict:
    exp_h = int((df["datetime"].max() - df["datetime"].min()).total_seconds() / 3600) + 1
    return {
        "label": label,
        "rows": int(len(df)),
        "expected_hours": int(exp_h),
        "coverage_pct": round(100 * len(df) / exp_h, 2) if exp_h > 0 else 0,
        "first": str(df["datetime"].min()),
        "last": str(df["datetime"].max()),
        "duration_days": int((df["datetime"].max() - df["datetime"].min()).total_seconds() / 86400),
    }


def main() -> None:
    print("=" * 60)
    print("  01b_merge_gap.py — Merge + re-split")
    print("=" * 60)

    print(f"\n[1] Load main: {MAIN}")
    main_df = load_main()
    print(f"    {len(main_df)} rows")

    print("\n[2] Load 8 zips")
    zips_df = load_zips()
    print(f"    {len(zips_df)} rows from zips")

    print("\n[3] Merge + dedupe")
    full = pd.concat([main_df, zips_df], ignore_index=True)
    before = len(full)
    full = full.drop_duplicates(subset=["open_time"], keep="first")
    after = len(full)
    print(f"    before: {before} | after: {after} | removed: {before - after}")

    print("\n[4] Sort + datetime")
    full = full.sort_values("open_time").reset_index(drop=True)
    full["datetime"] = pd.to_datetime(full["open_time"], unit="s")
    print(f"    first: {full['datetime'].min()}")
    print(f"    last:  {full['datetime'].max()}")

    print("\n[5] Gap report (post-merge)")
    gr = gap_report(full)
    print(f"    gaps > 1h:  {gr['count_gt_1h']}")
    print(f"    gaps > 24h: {gr['count_gt_24h']}")
    if gr["top5"]:
        print("    TOP 5:")
        for i, g in enumerate(gr["top5"], 1):
            print(f"      {i}. {g['from']} → {g['to']}  ({g['hours']}h)")

    print(f"\n[6] Save: {OUT_DIR}/BTCUSDT_1h_full.csv")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    full[["datetime", "open", "high", "low", "close", "volume"]].to_csv(
        OUT_DIR / "BTCUSDT_1h_full.csv", index=False)
    print(f"    {len(full)} rows saved")

    print("\n[7] 3-way split")
    train = full[full["datetime"] <= TRAIN_END].copy()
    val = full[(full["datetime"] > TRAIN_END) & (full["datetime"] <= VAL_END)].copy()
    test = full[full["datetime"] > VAL_END].copy()

    train_s = split_stats(train, "TRAIN")
    val_s = split_stats(val, "VAL")
    test_s = split_stats(test, "TEST")
    for s in (train_s, val_s, test_s):
        print(f"    {s['label']:6s}: {s['rows']:5d} rows | "
              f"coverage {s['coverage_pct']:5.1f}% | "
              f"{s['first']} → {s['last']} | {s['duration_days']}d")

    print("\n[8] Save train/val/test + metadata")
    cols = ["datetime", "open", "high", "low", "close", "volume"]
    train[cols].to_csv(OUT_DIR / "train.csv", index=False)
    val[cols].to_csv(OUT_DIR / "val.csv", index=False)
    test[cols].to_csv(OUT_DIR / "test.csv", index=False)
    print(f"    train.csv: {len(train)} | val.csv: {len(val)} | test.csv: {len(test)}")

    metadata = {
        "input_main": str(MAIN),
        "input_zips": MONTHS,
        "output": str(OUT_DIR / "BTCUSDT_1h_full.csv"),
        "total_rows": int(len(full)),
        "merge": {
            "before_dedupe": before,
            "after_dedupe": after,
            "removed": before - after,
        },
        "split_boundaries": {"train_end": str(TRAIN_END), "val_end": str(VAL_END)},
        "stats": {"train": train_s, "val": val_s, "test": test_s},
        "gap_report": gr,
    }
    with open(OUT_DIR / "split_metadata_full.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False, default=str)
    print("    split_metadata_full.json written")

    print("\n" + "=" * 60)
    print("  ✅ DONE")
    print("=" * 60)


if __name__ == "__main__":
    main()
