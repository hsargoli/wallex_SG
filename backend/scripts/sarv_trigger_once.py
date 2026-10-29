"""One-shot SarvRouter tick — production kickoff."""
import sys
from pathlib import Path
_BACKEND = Path(__file__).resolve().parent.parent
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

import csv
from decimal import Decimal
from app.domain.entities.candle import Candle
from app.services.bots.sarv_router.bot import SarvRouter
from app.services.bots.sarv_router.config import SarvRouterConfig
from app.services.bots.sarv_router.store import SarvStore
from app.services.bots.sarv_router.audit import AuditTrail
from app.services.bots.sarv_router.gate import DEFAULT_PATH


def load_recent(n: int = 300) -> list[Candle]:
    path = _BACKEND / "data" / "candles" / "historical" / "BTCUSDT_1h.csv"
    out = []
    with open(path) as f:
        for row in csv.DictReader(f):
            ts = int(row["open_time"])
            if ts > 10_000_000_000:
                ts //= 1000
            out.append(Candle(
                time=ts, open=Decimal(row["open"]), high=Decimal(row["high"]),
                low=Decimal(row["low"]), close=Decimal(row["close"]),
                volume=Decimal(row["volume"]),
            ))
    return out[-n:]


def main():
    cs = load_recent()
    print(f"loaded {len(cs)} recent candles (last ts={cs[-1].time})")

    router = SarvRouter(
        config=SarvRouterConfig(),
        start_bot=lambda s: print(f"  → start_bot({s})"),
        stop_bot=lambda s: None,
        stop_all=lambda: print("  → stop_all()"),
        store=SarvStore(),
        audit=AuditTrail(),
    )
    r = router.tick("production-default", cs, now_idx=len(cs) - 1)
    print(f"\ntick result: {r}")
    print(f"\ngate file: {DEFAULT_PATH}")
    if DEFAULT_PATH.exists():
        print(f"gate content:\n{DEFAULT_PATH.read_text()}")


if __name__ == "__main__":
    main()
