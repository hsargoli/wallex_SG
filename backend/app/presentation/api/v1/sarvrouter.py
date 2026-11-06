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

# ─── Backtest Builder (ADR-0035) ─────────────────────────────────────
import sys
from pathlib import Path
from decimal import Decimal
from typing import Any
from pydantic import BaseModel
from app.domain.entities.candle import Candle
from app.services.bots.sarv_router.bot import SarvRouter
from app.services.bots.sarv_router.config import SarvRouterConfig
from app.services.bots.sarv_router.store import SarvStore
from app.services.bots.sarv_router.audit import AuditTrail
from app.services.bots.sarv_router.backtest_adapter import run_sarv_backtest

_DATA_FILE = Path(__file__).resolve().parent.parent.parent.parent.parent / "data" / "candles" / "historical" / "BTCUSDT_1h.csv"

class SarvBacktestInput(BaseModel):
    stability_window: int = 36
    cooldown_candles: int = 12
    uptrend_adx_min: float = 25.0
    downtrend_adx_min: float = 25.0
    cash_reserve_pct: float = 10.0
    daily_loss_limit_pct: float = 2.0

def _load_candles() -> list[Candle]:
    import pandas as pd
    if not _DATA_FILE.exists():
        return []
    df = pd.read_csv(_DATA_FILE)
    # Handle mixed timestamps (10-digit or 13-digit)
    # Reuse logic from AP-62
    times = df["open_time"].apply(lambda x: int(x) // 1000 if int(x) > 10**12 else int(x))
    return [
        Candle(
            time=int(times.iloc[i]),
            open=Decimal(str(r["open"])),
            high=Decimal(str(r["high"])),
            low=Decimal(str(r["low"])),
            close=Decimal(str(r["close"])),
            volume=Decimal(str(r["volume"]))
        )
        for i, r in df.iterrows()
    ]

@router.post("/backtest")
async def sarvrouter_backtest(body: SarvBacktestInput) -> dict:
    """Run backtest with user's config, compare to default."""
    try:
        candles = _load_candles()
        if not candles:
            raise HTTPException(503, detail="Historical data missing")
        # Limit to last 10,000 candles (approx 1 year) to prevent proxy timeout
        candles = candles[-10000:]
    except Exception as e:
        raise HTTPException(500, detail=f"Data load failed: {str(e)}")

    try:
        # 1. Run default
        def run_cfg(cfg: SarvRouterConfig) -> dict:
            import tempfile
            tmp = Path(tempfile.mkdtemp())
            router = SarvRouter(
                config=cfg, start_bot=lambda s: None, stop_bot=lambda s: None,
                stop_all=lambda: None, store=SarvStore(base_dir=tmp), audit=AuditTrail(base_dir=tmp)
            )
            res = run_sarv_backtest(router, "builder", candles)
            
            # Compute accuracy
            correct, total = 0, 0
            for i, regime in enumerate(res["regime_sequence"]):
                if regime in ("uptrend", "downtrend", "range") and i + 24 < len(candles):
                    fwd_ret = (float(candles[i+24].close) / float(candles[i].close) - 1) * 100
                    total += 1
                    if regime == "uptrend" and fwd_ret > 0: correct += 1
                    elif regime == "downtrend" and fwd_ret < 0: correct += 1
                    elif regime == "range" and abs(fwd_ret) < 1.0: correct += 1
                    
            acc = (correct / total * 100) if total > 0 else 0.0
            return {
                "switches": res["switches"],
                "accuracy": round(acc, 1),
                "total_signals": total,
                "correct": correct,
            }

        default_res = run_cfg(SarvRouterConfig())
        
        # 2. Run custom
        custom_cfg = SarvRouterConfig(
            stability_window=body.stability_window,
            cooldown_candles=body.cooldown_candles,
            uptrend_adx_min=body.uptrend_adx_min,
            downtrend_adx_min=body.downtrend_adx_min,
            cash_reserve_pct=body.cash_reserve_pct,
            daily_loss_limit_pct=body.daily_loss_limit_pct,
        )
        custom_res = run_cfg(custom_cfg)

        # 3. Compare
        delta = round(custom_res["accuracy"] - default_res["accuracy"], 1)
        switch_delta = round((custom_res["switches"] / max(default_res["switches"], 1) - 1) * 100, 1)
        
        warnings = []
        if abs(switch_delta) > 30:
            warnings.append(f"⚠️ تعداد switchها {switch_delta:+.1f}% تغییر کرد.")
        
        return {
            "default": default_res,
            "custom": custom_res,
            "delta": {
                "accuracy": delta,
                "switches_pct": switch_delta,
            },
            "warnings": warnings,
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(500, detail=str(e))
