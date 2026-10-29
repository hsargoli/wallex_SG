"""SarvRouter — real backtest on BTCUSDT (mock bot callbacks).

Usage:
    python scripts/sarv_router_backtest.py --csv <path> --period "2022-04-01:2022-07-01"
"""
import argparse, csv, sys, uuid
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

_BACKEND = Path(__file__).resolve().parent.parent
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from app.domain.entities.candle import Candle
from app.services.bots.sarv_router.audit import AuditTrail
from app.services.bots.sarv_router.backtest_adapter import run_sarv_backtest
from app.services.bots.sarv_router.bot import SarvRouter
from app.services.bots.sarv_router.config import SarvRouterConfig
from app.services.bots.sarv_router.store import SarvStore


def _ts(s):
    return int(datetime.fromisoformat(s).replace(tzinfo=timezone.utc).timestamp())


def load_candles(path, start, end):
    s_ts, e_ts = _ts(start), _ts(end)
    out = []
    with open(path) as f:
        for row in csv.DictReader(f):
            ts = int(row["open_time"])
            if ts > 10_000_000_000:
                ts //= 1000
            if s_ts <= ts < e_ts:
                out.append(Candle(
                    time=ts,
                    open=Decimal(row["open"]),
                    high=Decimal(row["high"]),
                    low=Decimal(row["low"]),
                    close=Decimal(row["close"]),
                    volume=Decimal(row["volume"]),
                ))
    return out


def run_period(csv_path, label, start, end, tmp_dir):
    candles = load_candles(csv_path, start, end)
    if not candles:
        return {"label": label, "error": "no data"}

    calls = {"start": [], "stop_all": 0}
    def _start(slug): calls["start"].append(slug)
    def _stop(slug): pass
    def _stop_all(): calls["stop_all"] += 1

    uid = str(uuid.uuid4())
    store = SarvStore(base_dir=tmp_dir)
    audit = AuditTrail(base_dir=tmp_dir)
    router = SarvRouter(
        config=SarvRouterConfig(),
        start_bot=_start, stop_bot=_stop, stop_all=_stop_all,
        store=store, audit=audit,
    )
    result = run_sarv_backtest(router, uid, candles)

    # Regime distribution
    from collections import Counter
    dist = Counter(result["regime_sequence"])

    return {
        "label": label,
        "candles": len(candles),
        "switches": result["switches"],
        "kill_events": result["kill_events"],
        "final_regime": result["final_regime"],
        "final_active_bots": result["final_active_bots"],
        "final_cash": result["final_cash"],
        "regime_dist": dict(dist),
        "bot_starts": calls["start"],
        "stop_all_calls": calls["stop_all"],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True)
    ap.add_argument("--period", action="append", required=True)
    args = ap.parse_args()

    import tempfile
    tmp = Path(tempfile.mkdtemp())

    print("=" * 78)
    print(f"SARVROUTER BACKTEST — {Path(args.csv).name}")
    print("=" * 78)

    for p in args.period:
        start, end = p.split(":")
        label = f"{start[:7]}..{end[:7]}"
        r = run_period(args.csv, label, start, end, tmp)
        print(f"\n>> {label}")
        if "error" in r:
            print(f"   ERROR: {r['error']}")
            continue
        print(f"   candles={r['candles']}  switches={r['switches']}  kill={r['kill_events']}")
        print(f"   final_regime={r['final_regime']}  active_bots={r['final_active_bots']}")
        print(f"   final_cash={r['final_cash']:,.0f}")
        print(f"   bot_starts={r['bot_starts']}")
        print(f"   regime_dist (candles per regime):")
        for regime, count in sorted(r["regime_dist"].items(), key=lambda x: -x[1]):
            pct = count / r["candles"] * 100
            print(f"     {regime:10s}: {count:4d} ({pct:.1f}%)")
    print("\n" + "=" * 78)


if __name__ == "__main__":
    main()
