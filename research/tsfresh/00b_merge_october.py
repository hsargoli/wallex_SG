"""00b_merge_october.py — Merge Oct 2026 zip with existing CSV.

Fallback when Binance API is geo-blocked.
"""
from __future__ import annotations

import zipfile
from pathlib import Path

import pandas as pd

ZIP = Path("backend/data/candles/zips/BTCUSDT/BTCUSDT-1h-2026-10.zip")
DATA = Path("research/tsfresh/data/BTCUSDT_1h_full.csv")

COLS = ["open_time", "open", "high", "low", "close", "volume",
        "ct", "qv", "cnt", "tbb", "tbq", "ig"]


def main() -> None:
    print("=" * 60)
    print("  00b_merge_october.py")
    print("=" * 60)

    if not ZIP.exists():
        raise SystemExit(f"❌ zip not found: {ZIP}")
    if not DATA.exists():
        raise SystemExit(f"❌ data not found: {DATA}")

    df = pd.read_csv(DATA)
    df["datetime"] = pd.to_datetime(df["datetime"])
    print(f"[1] Loaded {len(df)} rows | last: {df['datetime'].iloc[-1]}")

    print(f"\n[2] Extract: {ZIP.name}")
    with zipfile.ZipFile(ZIP) as z:
        name = z.namelist()[0]
        with z.open(name) as f:
            oct_df = pd.read_csv(f, header=None, names=COLS)
    print(f"    {len(oct_df)} rows")

    oct_df = oct_df[["open_time", "open", "high", "low", "close", "volume"]].copy()
    # Binance raw: open_time in ms → use unit="ms" directly
    # AP-62: explicit unit by digit count (not heuristic)
    _ts_digits = len(str(int(oct_df["open_time"].iloc[0])))
    _UNIT_MAP = {10: "s", 13: "ms", 16: "us"}
    if _ts_digits not in _UNIT_MAP:
        raise ValueError(f"Unknown timestamp unit: {_ts_digits} digits")
    oct_df["datetime"] = pd.to_datetime(oct_df["open_time"].astype("int64"), unit=_UNIT_MAP[_ts_digits])
    oct_df = oct_df.drop(columns=["open_time"])
    print(f"    first: {oct_df['datetime'].iloc[0]} | last: {oct_df['datetime'].iloc[-1]}")

    print("\n[3] Merge (dedupe)")
    full = pd.concat([df, oct_df], ignore_index=True)
    full = full.drop_duplicates(subset=["datetime"], keep="last").sort_values("datetime").reset_index(drop=True)
    print(f"    merged: {len(full)} rows | last: {full['datetime'].iloc[-1]}")

    print(f"\n[4] Save: {DATA}")
    full.to_csv(DATA, index=False)
    print(f"    saved")
    print("\n✅ DONE")


if __name__ == "__main__":
    main()
