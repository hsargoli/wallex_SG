"""Fetch hourly candles from Wallex and persist to CSV.

Idempotent: existing CSV is merged with fresh data, newer wins,
rows sorted by open_time. Safe to run multiple times per day.

Usage (from ~/wallex/backend):
    uv run python -m scripts.fetch_candles
"""

import asyncio
import csv
import logging
from pathlib import Path

from app.application.use_cases.get_candles import GetCandlesUseCase
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.infrastructure.exchange.wallex.client import WallexExchange

log = logging.getLogger(__name__)

# ── Configuration ──
SYMBOLS = ["BTCTMN", "ETHTMN", "USDTTMN"]
TIMEFRAME = "1h"
LIMIT = 700  # 29 days ≈ 696; ask for 700
DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "candles"
HEADER = ["open_time", "open", "high", "low", "close", "volume"]

Row = tuple[str, str, str, str, str]


def load_existing(path: Path) -> dict[int, Row]:
    """Read existing CSV into {open_time: (o,h,l,c,v)}. Missing or bad header → {}."""
    if not path.exists():
        return {}
    rows: dict[int, Row] = {}
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        header = next(reader, None)
        if header != HEADER:
            log.warning("%s: header mismatch %r — treating as empty", path.name, header)
            return {}
        for row in reader:
            if len(row) == 6:
                rows[int(row[0])] = (row[1], row[2], row[3], row[4], row[5])
    return rows


def write_csv(path: Path, rows: dict[int, Row]) -> None:
    """Atomic write: temp file + os.replace."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".csv.tmp")
    with tmp.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(HEADER)
        for ts in sorted(rows):
            w.writerow([ts, *rows[ts]])
    tmp.replace(path)


async def fetch_one(uc: GetCandlesUseCase, symbol: str) -> dict[int, Row]:
    """Fetch candles for one symbol → dict keyed by open_time."""
    candles = await uc.execute(symbol=symbol, timeframe=TIMEFRAME, limit=LIMIT)
    return {
        c.time: (str(c.open), str(c.high), str(c.low), str(c.close), str(c.volume))
        for c in candles
    }


async def main() -> None:
    configure_logging()
    settings = get_settings()
    exchange = WallexExchange.create(settings)
    uc = GetCandlesUseCase(exchange=exchange)

    try:
        for symbol in SYMBOLS:
            path = DATA_DIR / f"{symbol}_{TIMEFRAME}.csv"
            existing = load_existing(path)
            try:
                fresh = await fetch_one(uc, symbol)
            except Exception as e:
                log.error("%s: fetch failed — %s", symbol, e)
                continue
            merged = {**existing, **fresh}  # fresh wins on overlap
            added = len(merged) - len(existing)
            write_csv(path, merged)
            log.info(
                "%s  existing=%d  fresh=%d  new=%+d  total=%d  → %s",
                symbol, len(existing), len(fresh), added, len(merged), path.name,
            )
    finally:
        await exchange.aclose()


if __name__ == "__main__":
    asyncio.run(main())
