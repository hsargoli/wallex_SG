"""A/B test for SarvRouter regime config — compare to baseline.

Usage:
    python scripts/regime_ab_test.py --save-baseline
    python scripts/regime_ab_test.py --stability 36
    python scripts/regime_ab_test.py --cooldown 24
    python scripts/regime_ab_test.py --uptrend-adx 30 --downtrend-adx 30
"""
import argparse, csv, json, sys, tempfile, uuid
from collections import Counter
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

DATA = _BACKEND / "data" / "candles" / "historical" / "BTCUSDT_1h.csv"
BASELINE = _BACKEND.parent / "docs" / "reports" / "backtest" / "BASELINE_REGIME.json"
PERIODS = [
    ("Q2-2022", "2022-04-01", "2022-07-01"),
    ("Q4-2023", "2023-10-01", "2024-01-01"),
    ("Q1-2024", "2024-01-01", "2024-04-01"),
]


def _ts(s):
    return int(datetime.fromisoformat(s).replace(tzinfo=timezone.utc).timestamp())


def _load(path, start, end):
    s_ts, e_ts = _ts(start), _ts(end)
    out = []
    with open(path) as f:
        for row in csv.DictReader(f):
            ts = int(row["open_time"])
            if ts > 10_000_000_000:
                ts //= 1000
            if s_ts <= ts < e_ts:
                out.append(Candle(
                    time=ts, open=Decimal(row["open"]), high=Decimal(row["high"]),
                    low=Decimal(row["low"]), close=Decimal(row["close"]),
                    volume=Decimal(row["volume"]),
                ))
    return out


def _one(cfg, label, start, end):
    cs = _load(DATA, start, end)
    if not cs:
        return {"label": label, "error": "no data"}
    tmp = Path(tempfile.mkdtemp())
    router = SarvRouter(
        config=cfg, start_bot=lambda s: None,
        stop_bot=lambda s: None, stop_all=lambda: None,
        store=SarvStore(base_dir=tmp), audit=AuditTrail(base_dir=tmp),
    )
    r = run_sarv_backtest(router, str(uuid.uuid4()), cs)
    total = len(cs)
    dist = Counter(r["regime_sequence"])
    return {
        "label": label, "candles": total, "switches": r["switches"],
        "pct": {k: round(v / total * 100, 1) for k, v in dist.items()},
    }


def _all(cfg):
    return {l: _one(cfg, l, s, e) for l, s, e in PERIODS}


def _fmt(p):
    return f"up={p.get('uptrend',0):4.1f} down={p.get('downtrend',0):4.1f} range={p.get('range',0):4.1f} unk={p.get('unknown',0):4.1f}"


def _evaluate(base, cand):
    """Check 3 criteria per period. Returns (passed_count, total_count)."""
    passed = total = 0
    for label in base:
        if label not in cand or "error" in cand[label]:
            continue
        b, c = base[label], cand[label]
        total += 1
        ok = c["switches"] < 6
        passed += int(ok)
        print(f"  {label} switch:  base={b['switches']:2d}  cand={c['switches']:2d}  {'✅' if ok else '❌'}")

        if label == "Q2-2022":
            total += 1
            up_b = b["pct"].get("uptrend", 0)
            up_c = c["pct"].get("uptrend", 0)
            ok = up_c < 5.0
            passed += int(ok)
            print(f"  {label} up%:     base={up_b:5.1f}  cand={up_c:5.1f}  {'✅' if ok else '❌'}")

        total += 1
        unk_b = b["pct"].get("unknown", 0)
        unk_c = c["pct"].get("unknown", 0)
        ok = unk_c < 25.0
        passed += int(ok)
        print(f"  {label} unk%:    base={unk_b:5.1f}  cand={unk_c:5.1f}  {'✅' if ok else '❌'}")
    return passed, total


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--save-baseline", action="store_true")
    ap.add_argument("--stability", type=int)
    ap.add_argument("--cooldown", type=int)
    ap.add_argument("--uptrend-adx", type=float)
    ap.add_argument("--downtrend-adx", type=float)
    args = ap.parse_args()

    cfg = SarvRouterConfig()
    if args.stability is not None: cfg.stability_window = args.stability
    if args.cooldown is not None: cfg.cooldown_candles = args.cooldown
    if args.uptrend_adx is not None: cfg.uptrend_adx_min = args.uptrend_adx
    if args.downtrend_adx is not None: cfg.downtrend_adx_min = args.downtrend_adx

    print(f"CONFIG: stab={cfg.stability_window} cd={cfg.cooldown_candles} up={cfg.uptrend_adx_min} dn={cfg.downtrend_adx_min}")
    result = _all(cfg)

    if args.save_baseline:
        BASELINE.parent.mkdir(parents=True, exist_ok=True)
        BASELINE.write_text(json.dumps(result, indent=2))
        print(f"\n✅ BASELINE saved: {BASELINE}")
        for l, r in result.items():
            print(f"  {l}: sw={r['switches']:2d}  {_fmt(r['pct'])}")
        return

    if not BASELINE.exists():
        print(f"\n⚠️ No baseline — run --save-baseline first")
        for l, r in result.items():
            print(f"  {l}: sw={r['switches']:2d}  {_fmt(r['pct'])}")
        return

    base = json.loads(BASELINE.read_text())
    print("\n" + "=" * 70)
    print("A/B COMPARISON vs BASELINE")
    print("=" * 70)
    passed, total = _evaluate(base, result)
    print("=" * 70)
    print(f"PASSED: {passed}/{total}  → {'✅ KEEP' if passed == total else '❌ REVERT'}")
    print("=" * 70)


if __name__ == "__main__":
    main()
