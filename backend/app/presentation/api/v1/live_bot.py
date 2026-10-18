"""Live Bot endpoints — /v1/user/live-bot/*.

Manages human-in-the-loop signal, kill switch, and status for bear_hunter.

State: per-user JSON at data/bots/bear_hunter/users/{user_id}.json
- No in-memory cache (read-through every request; MVP per Di Darya review)
- Audit trail at {user_id}.audit.jsonl (kill/resume/signal)
- Single-writer pattern: this module writes state; runner (future) will
  read state.json + flags.json to act. Keeps state mutation authoritative.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Annotated, Literal, Optional

import structlog
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.presentation.api.v1.auth import require_user_token
from app.services.bots.bear_hunter.state import BearHunterState, StateStore
from app.services.bots.bear_hunter.paths import user_state_path, user_audit_path

log = structlog.get_logger("live_bot.api")
router = APIRouter(prefix="/user/live-bot", tags=["Live Bot"])

_STORES: dict[uuid.UUID, StateStore] = {}


def _get_store(user_id: uuid.UUID) -> StateStore:
    # Store instances are cheap and stateless; still memoized to avoid recreate
    if user_id not in _STORES:
        _STORES[user_id] = StateStore(
            path=str(user_state_path(user_id)),
        )
    return _STORES[user_id]


def _load_state(user_id: uuid.UUID) -> BearHunterState:
    """Read fresh from disk. No cache (MVP)."""
    return _get_store(user_id).load()


def _persist(user_id: uuid.UUID, state: BearHunterState) -> None:
    store = _get_store(user_id)
    if not state.initialized:
        store.bootstrap(state)
    else:
        store.save(state)


def _audit(user_id: uuid.UUID, action: str, reason: str = "", **extra) -> None:
    """Append audit entry. Never raises (audit must not break user action)."""
    try:
        log_path = user_audit_path(user_id)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "action": action,
            "reason": reason,
            **extra,
        }
        with log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception as e:  # noqa: BLE001
        log.warning("audit_write_failed", user_id=str(user_id), error=str(e))


class StatusResponse(BaseModel):
    bot_status: str
    signal_direction: Optional[str] = None
    signal_expires_at: Optional[datetime] = None
    signal_note: Optional[str] = None
    positions_count: int = 0
    trades_today: int = 0
    daily_volume_tmn: float = 0.0
    capital_tmn: float = 100_000.0
    waiting_liquidity_since: Optional[datetime] = None
    idle: bool = False
    is_killed: bool = False
    kill_reason: Optional[str] = None
    last_trade_at: Optional[datetime] = None


class SignalRequest(BaseModel):
    direction: Literal["bearish", "bullish", "neutral"]
    ttl_days: int = Field(10, ge=1, le=90)
    note: Optional[str] = Field(None, max_length=200)


class ReasonRequest(BaseModel):
    reason: str = Field(..., min_length=3, max_length=200)


class ResumeRequest(BaseModel):
    reason: str = Field(..., min_length=3, max_length=200)
    force: bool = Field(False, description="Required to reset kill_switch_auto (safety)")


def _to_response(state: BearHunterState) -> StatusResponse:
    hs = state.human_signal
    return StatusResponse(
        bot_status=state.bot_status,
        signal_direction=hs.direction if hs else None,
        signal_expires_at=hs.expires_at if hs else None,
        signal_note=hs.note if hs else None,
        positions_count=len(state.open_positions),
        trades_today=state.trades_today,
        daily_volume_tmn=state.daily_volume_tmn,
        capital_tmn=state.capital_tmn,
        waiting_liquidity_since=state.waiting_liquidity_since,
        idle=state.idle,
        is_killed=state.is_killed,
        kill_reason=state.kill_switch_reason,
        last_trade_at=state.last_trade_at,
    )


@router.get("/status", response_model=StatusResponse)
async def get_status(
    user_id: Annotated[uuid.UUID, Depends(require_user_token)],
) -> StatusResponse:
    return _to_response(_load_state(user_id))


@router.post("/signal", response_model=StatusResponse)
async def set_signal(
    body: SignalRequest,
    user_id: Annotated[uuid.UUID, Depends(require_user_token)],
) -> StatusResponse:
    state = _load_state(user_id)
    try:
        state.set_signal(
            body.direction, body.ttl_days, set_by="endpoint", note=body.note,
        )
    except ValueError as e:
        raise HTTPException(400, detail=str(e))
    _persist(user_id, state)
    _audit(user_id, "signal", direction=body.direction, ttl_days=body.ttl_days)
    log.info("signal_set", user_id=str(user_id), direction=body.direction, ttl=body.ttl_days)
    return _to_response(state)


@router.post("/kill", response_model=StatusResponse)
async def kill_bot(
    body: ReasonRequest,
    user_id: Annotated[uuid.UUID, Depends(require_user_token)],
) -> StatusResponse:
    state = _load_state(user_id)
    state.mark_kill_switch(body.reason, source="manual")
    _persist(user_id, state)
    _audit(user_id, "kill", reason=body.reason)
    log.warning("bot_killed", user_id=str(user_id), reason=body.reason)
    return _to_response(state)


@router.post("/resume", response_model=StatusResponse)
async def resume_bot(
    body: ResumeRequest,
    user_id: Annotated[uuid.UUID, Depends(require_user_token)],
) -> StatusResponse:
    state = _load_state(user_id)
    was_killed = state.is_killed
    was_idle = state.idle
    # Safety: auto kill requires force=true (triggered by reconcile, corruption, etc.)
    if state.kill_switch_auto and not body.force:
        raise HTTPException(
            400,
            detail=(
                f"Auto kill switch active (reason: {state.kill_switch_reason or 'unknown'}). "
                f"Investigate before resuming. Pass force=true to override."
            ),
        )
    if was_killed:
        state.reset_kill_switch(body.reason)
    state.resume_from_idle()
    _persist(user_id, state)
    _audit(user_id, "resume", reason=body.reason, was_killed=was_killed, was_idle=was_idle)
    log.info("bot_resumed", user_id=str(user_id), reason=body.reason)
    return _to_response(state)
