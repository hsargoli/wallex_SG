"""SarvRouter API — status + kill switch.

Reads/writes:
    data/sarv_router/users/production-default.json  (state)
    data/sarv_router/gate.json                       (gate flag)

Kill switch = both files atomically:
    state.kill_switch_manual = True
    gate.allow_new_entries   = False

Reenable = reverse of both.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/sarvrouter", tags=["SarvRouter"])

SARV_DIR = Path("data") / "sarv_router"


def _state_file() -> Path:
    return SARV_DIR / "users" / "production-default.json"


def _gate_file() -> Path:
    return SARV_DIR / "gate.json"


def _load(path: Path) -> dict:
    if not path.exists():
        raise HTTPException(status_code=503, detail=f"missing file: {path}")
    try:
        return json.loads(path.read_text())
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"corrupt {path}: {e}")


def _write(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2))


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@router.get("/status")
async def get_status() -> dict:
    """SarvRouter status: state + gate."""
    state = _load(_state_file())
    gate = _load(_gate_file())
    return {
        "regime": state.get("current_regime", "unknown"),
        "regime_since_idx": state.get("regime_since_idx"),
        "last_switch_idx": state.get("last_switch_idx"),
        "active_bots": state.get("active_bots", []),
        "allocations": state.get("allocations", {}),
        "capital_total": state.get("total_capital", 0.0),
        "cash": state.get("cash", 0.0),
        "daily_pnl_pct": state.get("daily_pnl_pct", 0.0),
        "kill_switch_manual": state.get("kill_switch_manual", False),
        "kill_switch_auto": state.get("kill_switch_auto", False),
        "gate": gate,
    }


@router.post("/kill-switch")
async def kill_switch() -> dict:
    """Emergency stop: block new entries + mark state killed."""
    state = _load(_state_file())
    gate = _load(_gate_file())

    state["kill_switch_manual"] = True
    gate["allow_new_entries"] = False
    gate["updated_at"] = _now_iso()
    gate["killed_by"] = "manual"

    _write(_state_file(), state)
    _write(_gate_file(), gate)
    return {
        "ok": True,
        "action": "kill_switch_activated",
        "allow_new_entries": False,
        "updated_at": gate["updated_at"],
    }


@router.post("/reenable")
async def reenable() -> dict:
    """Re-enable new entries (clear manual kill)."""
    state = _load(_state_file())
    gate = _load(_gate_file())

    state["kill_switch_manual"] = False
    gate["allow_new_entries"] = True
    gate["updated_at"] = _now_iso()
    gate.pop("killed_by", None)

    _write(_state_file(), state)
    _write(_gate_file(), gate)
    return {
        "ok": True,
        "action": "reenabled",
        "allow_new_entries": True,
        "updated_at": gate["updated_at"],
    }
