"""00_fetch_recent.py — ⚠️ WIP, BLOCKED in Iran.

Binance API (api.binance.com) is not reachable from Iranian servers.
This script is kept for future use if API access becomes available.
Last attempt: 2026-11-03 (connection timeout).

See: research/tsfresh/REPORT.md (section 3, Binance microsecond anomaly)
"""
from __future__ import annotations

import json
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

DATA = Path("research/tsfresh/data/BTCUSDT_1h_full.csv")
API = "https://api.binance.com/api/v3/klines"

LIMIT = 500


def fetch_klines(limit: int = LIMIT) -> list:
    now = int(time.time())
    from_ts = now - limit * 3600
    url = f"{API}?symbol=BTCUSDT&interval=1h&startTime={from_ts*1000}&limit={limit}"
    print(f"  GET {url}")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15) as r:
        data = json.loads(r.read())
    return data


def main() -> None:
    print("=" * 60)
    print("  00_fetch_recent.py — Fetch last 500 BTCUSDT 1h")
    print("=" * 60)

    if not DATA.exists():
        raise SystemExit(f"❌ base data not found: {DATA}")

    df = pd.read_csv(DATA)
    df["datetime"] = pd.to_datetime(df["datetime"])
    print(f"[1] Loaded {len(df)} rows | last: {df['datetime'].iloc[-1]}")

    print("\n[2] Fetch from Binance API")
    try:
        klines = fetch_klines(LIMIT)
    except Exception as e:
        raise SystemExit(f"❌ fetch failed: {e}")
    print(f"    got {len(klines)} candles")

    rows = []
    for k in klines:
        rows.append({
            "datetime": pd.to_datetime(k[0], unit="ms"),
            "open": float(k[1]),
            "high": float(k[2]),
            "low": float(k[3]),
            "close": float(k[4]),
            "volume": float(k[5]),
        })
    recent = pd.DataFrame(rows)
    print(f"    last fetched: {recent['datetime'].iloc[-1]} | close={recent['close'].iloc[-1]}")

    print("\n[3] Merge (dedupe by datetime)")
    full = pd.concat([df, recent], ignore_index=True)
    full = full.drop_duplicates(subset=["datetime"], keep="last").sort_values("datetime").reset_index(drop=True)
    print(f"    merged: {len(full)} rows | last: {full['datetime'].iloc[-1]}")

    print(f"\n[4] Save: {DATA}")
    full.to_csv(DATA, index=False)
    print(f"    saved {len(full)} rows")

    print("\n✅ DONE")


if __name__ == "__main__":
    main()
