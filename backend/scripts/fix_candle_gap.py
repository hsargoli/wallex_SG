"""Fill missing 1h candles via forward-fill (volume=0).

Policy:
  - Small gaps (1-2 hours): forward-fill with volume=0 (no activity).
  - Large gaps (>2 hours): left untouched — analytics must handle.

Usage (from ~/wallex/backend):
    uv run python -m scripts.fix_candle_gap
"""

import csv
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "candles"
STEP = 3600
MAX_FFILL_HOURS = 2
HEADER = ["open_time", "open", "high", "low", "close", "volume"]


def read_existing(path: Path) -> dict[int, list[str]]:
    rows: dict[int, list[str]] = {}
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        header = next(reader)
        if header != HEADER:
            raise SystemExit(f"❌ {path.name}: bad header")
        for row in reader:
            if len(row) == 6:
                rows[int(row[0])] = row
    return rows


def write_atomic(path: Path, rows: dict[int, list[str]]) -> None:
    tmp = path.with_suffix(".csv.tmp")
    with tmp.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(HEADER)
        for ts in sorted(rows):
            w.writerow(rows[ts])
    tmp.replace(path)


def fill_one_file(path: Path) -> tuple[int, int]:
    """Return (gaps_small, gaps_large)."""
    rows = read_existing(path)
    times = sorted(rows)
    small: list[int] = []
    large: list[int] = []
    for i in range(1, len(times)):
        delta = times[i] - times[i - 1]
        if delta <= STEP:
            continue
        missing = list(range(times[i - 1] + STEP, times[i], STEP))
        if len(missing) <= MAX_FFILL_HOURS:
            small.extend(missing)
        else:
            large.extend(missing)

    if small:
        for ts in small:
            # Find previous candle (largest t < ts)
            prev_ts = max(t for t in times if t < ts)
            prev = rows[prev_ts]
            prev_close = prev[4]
            rows[ts] = [str(ts), prev_close, prev_close, prev_close, prev_close, "0"]
        write_atomic(path, rows)

    return len(small), len(large)


def main() -> None:
    files = sorted(DATA_DIR.glob("*_1h.csv"))
    if not files:
        print(f"❌ no *_1h.csv in {DATA_DIR}")
        return
    for path in files:
        small, large = fill_one_file(path)
        status = f"✅ +{small} ffill" if small else "no change"
        if large:
            status += f"  ⚠️  {large} large gaps (untouched)"
        print(f"{path.name:30} {status}")


if __name__ == "__main__":
    main()
