"""Room Hunter — detect price rooms (range consolidation). READ-ONLY."""
from __future__ import annotations
import argparse, csv, json, sys
from decimal import Decimal, InvalidOperation
from pathlib import Path

_BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_BACKEND))
from app.domain.entities.candle import Candle  # noqa: E402

CANDLES_DIR = _BACKEND / "data" / "candles"
COLS = {"open_time", "open", "high", "low", "close", "volume"}


def load_candles(symbol: str, timeframe: str) -> list[Candle]:
    path = CANDLES_DIR / f"{symbol}_{timeframe}.csv"
    if not path.is_file():
        raise SystemExit(f"ABORT: not found: {path}")
    out = []
    with path.open("r", encoding="utf-8", newline="") as f:
        r = csv.DictReader(f)
        if not COLS.issubset(r.fieldnames or set()):
            raise SystemExit(f"ABORT: bad cols: {r.fieldnames}")
        for ln, row in enumerate(r, 2):
            try:
                out.append(Candle(
                    time=int(row["open_time"]),
                    open=Decimal(row["open"]), high=Decimal(row["high"]),
                    low=Decimal(row["low"]), close=Decimal(row["close"]),
                    volume=Decimal(row["volume"]),
                ))
            except (ValueError, InvalidOperation) as e:
                raise SystemExit(f"ABORT: bad row line {ln}: {e}")
    if not out:
        raise SystemExit(f"ABORT: no rows in {path}")
    return out


def _count_clusters(indices: list[int]) -> int:
    """Count contiguous groups in a sorted list of indices."""
    if not indices:
        return 0
    n = 1
    for a, b in zip(indices, indices[1:]):
        if b - a > 1:
            n += 1
    return n


def detect_room(candles, window, tol_pct, min_touches) -> dict:
    if window < 2 or min_touches < 1 or tol_pct < 0:
        raise SystemExit("ABORT: invalid --window / --min-touches / --tolerance-pct")
    if len(candles) < window:
        raise SystemExit(f"ABORT: need >= {window}, got {len(candles)}")
    recent = candles[-window:]
    ceiling = max(c.high for c in recent)
    floor = min(c.low for c in recent)
    if floor <= 0:
        raise SystemExit(f"ABORT: floor <= 0: {floor}")
    tol = tol_pct / Decimal("100")
    ct = ceiling * (Decimal("1") - tol)
    ft = floor * (Decimal("1") + tol)
    ci = [i for i, c in enumerate(recent) if c.high >= ct]
    fi = [i for i, c in enumerate(recent) if c.low <= ft]
    ci_clusters = _count_clusters(ci)
    fi_clusters = _count_clusters(fi)
    detected = len(ci) >= min_touches and len(fi) >= min_touches
    return {
        "window": window, "tolerance_pct": str(tol_pct), "min_touches": min_touches,
        "candles_total": len(candles),
        "window_start_time": recent[0].time, "window_end_time": recent[-1].time,
        "ceiling": str(ceiling), "floor": str(floor),
        "range_pct": str((ceiling - floor) / floor * Decimal("100")),
        "ceiling_threshold": str(ct), "floor_threshold": str(ft),
        "ceiling_touches": len(ci), "floor_touches": len(fi),
        "ceiling_clusters": ci_clusters, "floor_clusters": fi_clusters,
        "ceiling_single_cluster": len(ci) >= 2 and ci_clusters == 1,
        "floor_single_cluster": len(fi) >= 2 and fi_clusters == 1,
        "ceiling_touch_times": [recent[i].time for i in ci],
        "floor_touch_times": [recent[i].time for i in fi],
        "room_detected": detected,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Room Hunter (READ-ONLY).")
    ap.add_argument("--symbol", required=True)
    ap.add_argument("--timeframe", default="1h")
    ap.add_argument("--window", type=int, default=50)
    ap.add_argument("--tolerance-pct", default="0.5")
    ap.add_argument("--min-touches", type=int, default=2)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    try:
        tol = Decimal(a.tolerance_pct)
    except InvalidOperation:
        raise SystemExit(f"ABORT: bad --tolerance-pct: {a.tolerance_pct!r}")
    candles = load_candles(a.symbol, a.timeframe)
    r = detect_room(candles, a.window, tol, a.min_touches)
    r["symbol"], r["timeframe"] = a.symbol, a.timeframe
    if a.json:
        print(json.dumps(r, ensure_ascii=False, indent=2))
    else:
        print(f"Symbol:        {a.symbol} {a.timeframe}")
        print(f"Window:        last {r['window']} of {r['candles_total']} candles")
        print(f"  from t={r['window_start_time']}  to t={r['window_end_time']}")
        print(f"Ceiling:       {r['ceiling']}")
        print(f"  threshold:   {r['ceiling_threshold']}  touches: {r['ceiling_touches']}")
        print(f"Floor:         {r['floor']}")
        print(f"  threshold:   {r['floor_threshold']}  touches: {r['floor_touches']}")
        print(f"Range:         {r['range_pct']}%")
        print(f"Tolerance:     ±{r['tolerance_pct']}%   Min touches/side: {r['min_touches']}")
        warn = r["ceiling_single_cluster"] or r["floor_single_cluster"]
        warn_txt = "  [WARNING: single-cluster touches - likely a trend, not a range]" if warn else ""
        print(f"Room detected: {'YES' if r['room_detected'] else 'no'}{warn_txt}")
    return 0 if r["room_detected"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
