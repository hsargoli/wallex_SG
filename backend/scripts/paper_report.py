"""Paper Mode weekly report — SarvRouter + nooaah + gate.

Usage:
    python scripts/paper_report.py              # last 7 days summary
    python scripts/paper_report.py --json       # raw JSON
"""
import argparse, json, sys
from pathlib import Path
from collections import Counter

_BACKEND = Path(__file__).resolve().parent.parent
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from app.services.bots.sarv_router.gate import read_gate

DATA = _BACKEND / "data"
SARV_USERS = DATA / "sarv_router" / "users"
NOOAAH_STATE = DATA / "nooaah" / "state.json"


def _load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def collect_sarv() -> dict:
    if not SARV_USERS.exists():
        return {"users": 0, "states": []}
    states = []
    for f in SARV_USERS.glob("*.json"):
        if ".audit." in f.name:
            continue
        d = _load_json(f)
        if d:
            states.append({"user": f.stem, **d})
    return {"users": len(states), "states": states}


def collect_nooaah() -> dict:
    state = _load_json(NOOAAH_STATE)
    if not state:
        return {"available": False}
    return {
        "available": True,
        "capital": state.get("capital_total", 0),
        "open_positions": len(state.get("open_positions", [])),
        "closed_trades": len(state.get("closed_trades", [])),
        "daily_pnl_pct": state.get("daily_pnl_pct", 0),
        "killed": state.get("killed", False),
    }


def summarize_gate_history(hours: int = 168) -> dict:
    """Read all audit logs, count gate writes in last N hours."""
    if not SARV_USERS.exists():
        return {}
    cutoff = __import__("time").time() - hours * 3600
    regimes = Counter()
    gate_open = 0
    gate_total = 0
    for f in SARV_USERS.glob("*.audit.jsonl"):
        for entry in _load_jsonl(f):
            ts_str = entry.get("timestamp", "")
            if not ts_str:
                continue
            try:
                from datetime import datetime
                ts = datetime.fromisoformat(ts_str).timestamp()
            except (ValueError, TypeError):
                continue
            if ts < cutoff:
                continue
            regime = entry.get("to_regime", "unknown")
            regimes[regime] += 1
            gate_total += 1
            if regime == "uptrend":
                gate_open += 1
    return {
        "hours": hours,
        "total_switches": gate_total,
        "regimes": dict(regimes),
        "gate_open_pct": round(gate_open / gate_total * 100, 1) if gate_total else 0,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    report = {
        "gate_now": {
            "allow_new_entries": read_gate().allow_new_entries,
            "regime": read_gate().regime,
        },
        "sarv_router": collect_sarv(),
        "nooaah": collect_nooaah(),
        "gate_history_7d": summarize_gate_history(168),
    }

    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False, default=str))
        return 0

    print("=" * 60)
    print("PAPER MODE REPORT — SarvRouter + nooaah")
    print("=" * 60)
    g = report["gate_now"]
    print(f"\n[GATE — now]")
    print(f"  allow_new_entries: {g['allow_new_entries']}")
    print(f"  regime: {g['regime']}")
    s = report["sarv_router"]
    print(f"\n[SARV ROUTER]")
    print(f"  active users: {s['users']}")
    for st in s["states"][:3]:
        print(f"  user {st['user'][:8]}: regime={st.get('current_regime')}, "
              f"bots={st.get('active_bots')}, cash={st.get('cash', 0):,.0f}")
    n = report["nooaah"]
    print(f"\n[NOOAAH]")
    if not n.get("available"):
        print(f"  state not found at {NOOAAH_STATE}")
    else:
        print(f"  capital: {n['capital']:,.0f}")
        print(f"  open positions: {n['open_positions']}")
        print(f"  closed trades: {n['closed_trades']}")
        print(f"  daily PnL: {n['daily_pnl_pct']:.2f}%")
        print(f"  killed: {n['killed']}")
    h = report["gate_history_7d"]
    print(f"\n[GATE HISTORY — last {h.get('hours', 168)}h]")
    print(f"  total switches: {h.get('total_switches', 0)}")
    print(f"  regimes: {h.get('regimes', {})}")
    print(f"  gate open: {h.get('gate_open_pct', 0)}%")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
