"""Fetch 1m candles from Wallex, 24h chunks, merge to CSV.

Wallex limits 1m to 24h per request. This script chunks backwards
from now, N days deep.

Usage (from ~/wallex/backend):
    uv run python -m scripts.fetch_candles_1m --days 20
    uv run python -m scripts.fetch_candles_1m --days 20 --symbols BTCTMN,ETHTMN
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import time
from pathlib import Path

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.domain.entities.candle import Candle
from app.infrastructure.exchange.wallex.client import WallexExchange
from app.services.bots.nooaah.bot import NooaahBot
from app.services.bots.nooaah.config import NooaahConfig

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "candles"
HEADER = ["open_time", "open", "high", "low", "close", "volume"]
CHUNK_HOURS = 24
DELAY_BETWEEN_REQUESTS = 0.05  # کوچیک، ولی polite


def load_existing(path: Path) -> dict[int, list[str]]:
    if not path.exists():
        return {}
    rows: dict[int, list[str]] = {}
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        header = next(reader, None)
        if header != HEADER:
            print(f"   ⚠️  {path.name}: header mismatch — recreating")
            return {}
        for row in reader:
            if len(row) == 6:
                rows[int(row[0])] = row
    return rows


def write_atomic(path: Path, rows: dict[int, list[str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".csv.tmp")
    with tmp.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(HEADER)
        for ts in sorted(rows):
            w.writerow(rows[ts])
    tmp.replace(path)


async def fetch_chunk(
    ex: WallexExchange, symbol: str, from_ts: int, to_ts: int
) -> list[Candle]:
    try:
        return await ex.get_candles(
            symbol=symbol,
            resolution="1",
            from_ts=from_ts,
            to_ts=to_ts,
        )
    except Exception as e:
        print(f"   ⚠️  {symbol} chunk [{from_ts}..{to_ts}]: {str(e)[:80]}")
        return []


async def fetch_symbol(
    ex: WallexExchange, symbol: str, days: int
) -> dict[int, list[str]]:
    path = DATA_DIR / f"{symbol}_1m.csv"
    existing = load_existing(path)
    print(f"  {symbol}: existing={len(existing)}")

    now = int(time.time())
    added = 0

    # chunks از قدیم به جدید (تا آپدیت تدریجی راحت‌تر باشه)
    for day_back in range(days, 0, -1):
        to_ts = now - (day_back - 1) * 24 * 3600
        from_ts = to_ts - CHUNK_HOURS * 3600

        candles = await fetch_chunk(ex, symbol, from_ts, to_ts)
        for c in candles:
            if c.time not in existing:
                existing[c.time] = [
                    str(c.time), str(c.open), str(c.high),
                    str(c.low), str(c.close), str(c.volume),
                ]
                added += 1
        await asyncio.sleep(DELAY_BETWEEN_REQUESTS)

    write_atomic(path, existing)
    print(f"  {symbol}: added={added}, total={len(existing)} → {path.name}")
    return existing


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=20)
    parser.add_argument("--symbols", default=None)
    parser.add_argument("--top", type=int, default=5)
    args = parser.parse_args()

    configure_logging()
    settings = get_settings()
    ex = WallexExchange.create(settings)

    try:
        if args.symbols:
            symbols = [s.strip() for s in args.symbols.split(",") if s.strip()]
        else:
            bot = NooaahBot(exchange=ex, config=NooaahConfig())
            symbols = await bot.pick_top_symbols(args.top)

        print(f"\n📥 Fetching {args.days} days × 1m for {len(symbols)} symbols")
        print(f"   chunks: {args.days} per symbol")
        print(f"   approx requests: {len(symbols) * args.days}\n")

        t0 = time.monotonic()
        for sym in symbols:
            await fetch_symbol(ex, sym, args.days)

        elapsed = time.monotonic() - t0
        print(f"\n✅ Done in {elapsed:.1f}s")
    finally:
        await ex.aclose()


if __name__ == "__main__":
    asyncio.run(main())
