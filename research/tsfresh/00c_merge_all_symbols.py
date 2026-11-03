"""00c_merge_all_symbols.py — Merge historical CSV + monthly zips for ETH, SOL.

Reuses the same normalization as BTCUSDT.
Output: data/{SYMBOL}_1h_full.csv for each symbol.

Binance timestamps: 13-digit (ms) pre-Oct-2026, 16-digit (us) from Oct-2026.
Handled via explicit UNIT_MAP (AP-62).
"""
from __future__ import annotations

import zipfile
from pathlib import Path

import pandas as pd

HIST_DIR = Path("backend/data/candles/historical")
ZIPS_BASE = Path("backend/data/candles/zips")
OUT_DIR = Path("research/tsfresh/data")

COLS = ["open_time", "open", "high", "low", "close", "volume",
        "ct", "qv", "cnt", "tbb", "tbq", "ig"]
UNIT_MAP = {10: "s", 13: "ms", 16: "us"}


def normalize_series_to_seconds(s):
    """Vectorized: handle 10-digit (s), 13-digit (ms), 16-digit (us). Returns seconds."""
    import numpy as np
    arr = s.astype("int64").to_numpy()
    arr = np.where(arr >= 10**15, arr // 1_000_000,
          np.where(arr >= 10**12, arr // 1_000, arr))
    return pd.Series(arr).astype("int64")

SYMBOLS = ["ETHUSDT", "SOLUSDT"]


def normalize_ts(ts_sample: int) -> str:
    digits = len(str(int(ts_sample)))
    if digits not in UNIT_MAP:
        raise ValueError(f"Unknown timestamp unit: {digits} digits (sample={ts_sample})")
    return UNIT_MAP[digits]


def load_historical(sym: str) -> pd.DataFrame:
    """Load historical CSV (already 6-column, but check timestamp format)."""
    f = HIST_DIR / f"{sym}_1h.csv"
    if not f.exists():
        raise SystemExit(f"❌ not found: {f}")
    df = pd.read_csv(f)
    if "datetime" in df.columns:
        df["datetime"] = pd.to_datetime(df["datetime"])
    elif "open_time" in df.columns:
        secs = normalize_series_to_seconds(df["open_time"])
        df["datetime"] = pd.to_datetime(secs, unit="s")
    else:
        raise SystemExit(f"❌ no datetime/open_time column in {f}")
    return df[["datetime", "open", "high", "low", "close", "volume"]]


def load_zips(sym: str) -> pd.DataFrame:
    """Load all zips for a symbol, extract OHLCV."""
    d = ZIPS_BASE / sym
    if not d.exists():
        return pd.DataFrame()
    zips = sorted(d.glob("*.zip"))
    if not zips:
        return pd.DataFrame()

    parts = []
    for z in zips:
        try:
            with zipfile.ZipFile(z) as zf:
                name = zf.namelist()[0]
                with zf.open(name) as f:
                    raw = pd.read_csv(f, header=None, names=COLS)
            secs = normalize_series_to_seconds(raw["open_time"])
            dt = pd.to_datetime(secs, unit="s")
            chunk = pd.DataFrame({
                "datetime": dt,
                "open": raw["open"], "high": raw["high"],
                "low": raw["low"], "close": raw["close"], "volume": raw["volume"],
            })
            parts.append(chunk)
        except Exception as e:
            print(f"  ⚠️ {z.name} skipped: {e}")
    if not parts:
        return pd.DataFrame()
    return pd.concat(parts, ignore_index=True)


def process(sym: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"  {sym}")
    print(f"{'=' * 60}")

    print(f"[1] Load historical CSV")
    hist = load_historical(sym)
    print(f"    {len(hist)} rows | {hist['datetime'].min()} → {hist['datetime'].max()}")

    print(f"[2] Load zips")
    zips = load_zips(sym)
    print(f"    {len(zips)} rows from zips")
    if len(zips) > 0:
        print(f"    range: {zips['datetime'].min()} → {zips['datetime'].max()}")

    print(f"[3] Merge + dedupe")
    full = pd.concat([hist, zips], ignore_index=True)
    before = len(full)
    full = full.drop_duplicates(subset=["datetime"], keep="last")
    full = full.sort_values("datetime").reset_index(drop=True)
    print(f"    before: {before} → after: {len(full)} (removed {before - len(full)})")
    print(f"    final range: {full['datetime'].min()} → {full['datetime'].max()}")

    out = OUT_DIR / f"{sym}_1h_full.csv"
    full.to_csv(out, index=False)
    print(f"[4] Saved: {out} ({len(full)} rows)")


def main() -> None:
    print("=" * 60)
    print("  00c_merge_all_symbols.py")
    print("=" * 60)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for sym in SYMBOLS:
        process(sym)
    print("\n✅ DONE")


if __name__ == "__main__":
    main()
