"""
BearHunter State — mutable runtime state with persistence.
Includes HumanSignal (datetime-based) for explicit user-set regime.
Migration: legacy current_regime=bear without human_signal → kill switch.
"""
import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List, Literal
from app.domain.ports.margin_exchange import MarginPosition

logger = logging.getLogger(__name__)

def utcnow() -> datetime:
    return datetime.now(timezone.utc)

STATE_VERSION = 1

_DT_FIELDS = {
    "kill_switch_activated_at", "paper_started_at",
    "last_user_seen_at", "last_trade_at", "last_reconciled_at", "last_presence_alert_at", "waiting_liquidity_since",
}


@dataclass(frozen=True)
class HumanSignal:
    """Explicit human-set direction. Replaces the old `current_regime` field."""
    direction: Literal["bearish", "bullish", "neutral"]
    set_at: datetime
    expires_at: datetime
    set_by: Literal["dashboard", "endpoint", "cli", "test"]
    note: Optional[str] = None

    def is_expired(self) -> bool:
        return utcnow() >= self.expires_at


@dataclass
class BearHunterState:
    version: int = STATE_VERSION
    initialized: bool = False

    kill_switch_auto: bool = False
    kill_switch_manual: bool = False
    kill_switch_reason: Optional[str] = None
    kill_switch_activated_at: Optional[datetime] = None

    paper_mode: bool = True
    paper_started_at: Optional[datetime] = None
    paper_days_elapsed: int = 0

    human_signal: Optional[HumanSignal] = None
    last_user_seen_at: Optional[datetime] = None
    last_presence_alert_at: Optional[datetime] = None
    idle: bool = False

    daily_volume_tmn: float = 0.0
    trades_today: int = 0
    daily_pnl_pct: float = 0.0
    pnl_8h_pct: float = 0.0
    last_trade_at: Optional[datetime] = None
    last_known_liquidity: dict = field(default_factory=dict)
    waiting_liquidity_since: Optional[datetime] = None

    capital_tmn: float = 100_000.0
    open_positions: List[MarginPosition] = field(default_factory=list)
    last_reconciled_at: Optional[datetime] = None

    def __post_init__(self):
        if self.paper_mode and self.paper_started_at is None:
            self.paper_started_at = utcnow()

    @property
    def current_regime(self) -> str:
        if not self.human_signal:
            return "idle"
        return {
            "bearish": "bear",
            "bullish": "bull",
            "neutral": "range",
        }.get(self.human_signal.direction, "idle")

    @property
    def is_waiting_liquidity(self) -> bool:
        return self.waiting_liquidity_since is not None

    @property
    def bot_status(self) -> str:
        """Derived status for UI/debug. Order matters: most severe first."""
        if self.kill_switch_auto:
            return "killed_auto"
        if self.kill_switch_manual:
            return "killed_manual"
        if self.idle:
            return "idle"
        if not self.human_signal:
            return "no_signal"
        if self.human_signal.is_expired():
            return "signal_expired"
        if self.human_signal.direction != "bearish":
            return "signal_not_bearish"
        if self.is_waiting_liquidity:
            return "waiting_liquidity"
        return "active"

    def set_signal(self, direction: str, ttl_days: int, set_by: str = "test", note: Optional[str] = None) -> None:
        """Set/replace human signal. Only updates state — does NOT close open positions."""
        if direction not in ("bearish", "bullish", "neutral"):
            raise ValueError(f"Invalid direction: {direction!r}.")
        if ttl_days <= 0 or ttl_days > 90:
            raise ValueError(f"Invalid ttl_days: {ttl_days}. Must be 1-90.")
        if set_by not in ("dashboard", "endpoint", "cli", "test"):
            raise ValueError(f"Invalid set_by: {set_by!r}.")
        now = utcnow()
        self.human_signal = HumanSignal(
            direction=direction,  # type: ignore[arg-type]
            set_at=now,
            expires_at=now + _days(ttl_days),
            set_by=set_by,  # type: ignore[arg-type]
            note=note,
        )
        self.waiting_liquidity_since = None

    @property
    def is_killed(self) -> bool:
        return self.kill_switch_auto or self.kill_switch_manual

    def mark_kill_switch(self, reason: str, source: str = "auto") -> None:
        if source == "auto":
            self.kill_switch_auto = True
        else:
            self.kill_switch_manual = True
        self.kill_switch_reason = reason
        self.kill_switch_activated_at = utcnow()

    def reset_kill_switch(self, reason: str) -> None:
        self.kill_switch_auto = False
        self.kill_switch_manual = False
        self.kill_switch_reason = f"manually_reset: {reason}"
        self.kill_switch_activated_at = None

    def mark_waiting_liquidity(self) -> None:
        """Set when dry_run returns NO_LIQUIDITY. Auto-cleared on success."""
        if self.waiting_liquidity_since is None:
            self.waiting_liquidity_since = utcnow()

    def clear_waiting_liquidity(self) -> None:
        """Clear on dry_run success or signal change."""
        self.waiting_liquidity_since = None

    def go_idle(self, reason: str = "manual") -> None:
        """Explicit idle. Bot will not trade until resume_from_idle()."""
        self.idle = True
        logger.info(f"went idle: {reason}")

    def resume_from_idle(self) -> None:
        """User explicitly resumes. Does NOT clear kill_switch or waiting_liquidity."""
        self.idle = False
        logger.info("resumed from idle")

    def reset_daily_stats(self) -> None:
        self.daily_volume_tmn = 0.0
        self.trades_today = 0
        self.daily_pnl_pct = 0.0

    def update_paper_days(self) -> None:
        if self.paper_started_at and self.paper_mode:
            self.paper_days_elapsed = (utcnow() - self.paper_started_at).days

    def recompute_rolling_stats(self, trades_8h: list, trades_today: list) -> None:
        self.pnl_8h_pct = sum(t.get("pnl_pct", 0) for t in trades_8h) if trades_8h else 0.0
        self.daily_pnl_pct = sum(t.get("pnl_pct", 0) for t in trades_today) if trades_today else 0.0

    def to_dict(self) -> dict:
        def _ser(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            if isinstance(obj, list):
                return [_ser(i) for i in obj]
            if isinstance(obj, dict):
                return {k: _ser(v) for k, v in obj.items()}
            return obj
        return _ser(asdict(self))

    @classmethod
    def from_dict(cls, data: dict) -> "BearHunterState":
        def _deser(obj, parent_key=None):
            if isinstance(obj, str):
                if parent_key in _DT_FIELDS:
                    try:
                        return datetime.fromisoformat(obj)
                    except ValueError:
                        return None
                return obj
            if isinstance(obj, list):
                return [_deser(i) for i in obj]
            if isinstance(obj, dict):
                return {k: _deser(v, k) for k, v in obj.items()}
            return obj
        data = _deser(data)

        # ─── Migration: legacy 'current_regime' ───
        legacy_regime = None
        if "current_regime" in data:
            legacy_regime = data.pop("current_regime")
            logger.warning(f"migration: dropped legacy current_regime={legacy_regime!r}")

        # ─── Reconstruct human_signal (datetime inside) ───
        if data.get("human_signal"):
            try:
                hs = data["human_signal"]
                for k in ("set_at", "expires_at"):
                    if isinstance(hs.get(k), str):
                        hs[k] = datetime.fromisoformat(hs[k])
                data["human_signal"] = HumanSignal(**hs)
            except (TypeError, ValueError) as e:
                logger.warning(f"failed to reconstruct human_signal: {e}")
                data["human_signal"] = None

        # ─── Reconstruct open_positions ───
        if data.get("open_positions"):
            valid = []
            for p in data["open_positions"]:
                try:
                    valid.append(MarginPosition(**p))
                except TypeError as e:
                    logger.warning(f"skip position (schema mismatch): {e}")
            data["open_positions"] = valid

        state = cls(**data)

        # ─── Kill switch on silent data loss ───
        if legacy_regime == "bear" and state.human_signal is None:
            state.mark_kill_switch("legacy_bear_without_human_signal", source="auto")
            logger.critical("migration: legacy bear regime without human_signal → KILL SWITCH")

        return state


def _days(n: int):
    from datetime import timedelta
    return timedelta(days=n)


class StateStore:
    def __init__(self, path: str = "backend/data/bots/bear_hunter/state.json", max_backups: int = 100):
        self.path = Path(path)
        self.backup_dir = self.path.parent / "backups"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.max_backups = max_backups

    def load(self) -> BearHunterState:
        if not self.path.exists():
            return BearHunterState()
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            file_version = raw.get("version", 1)
            if file_version > STATE_VERSION:
                state = BearHunterState()
                state.mark_kill_switch(f"state_version_too_new: v{file_version}", source="auto")
                return state
            return BearHunterState.from_dict(raw["state"])
        except (json.JSONDecodeError, KeyError, ValueError, TypeError) as e:
            logger.error(f"state.json corrupted: {e}")
            state = BearHunterState()
            state.mark_kill_switch(f"state_file_corrupted: {e}", source="auto")
            return state

    def _write_atomic(self, state: BearHunterState) -> None:
        tmp = self.path.with_suffix(".json.tmp")
        tmp.write_text(
            json.dumps({
                "version": STATE_VERSION,
                "saved_at": utcnow().isoformat(),
                "state": state.to_dict(),
            }, indent=2, ensure_ascii=False, default=str),
            encoding="utf-8",
        )
        tmp.replace(self.path)

    def bootstrap(self, state: BearHunterState) -> None:
        if state.initialized:
            raise ValueError("already bootstrapped")
        state.initialized = True
        self._write_atomic(state)

    def save(self, state: BearHunterState) -> None:
        if not state.initialized:
            logger.warning("save() skipped: not initialized")
            return
        if self.path.exists():
            ts = utcnow().strftime("%Y%m%d-%H%M%S")
            backup = self.backup_dir / f"state-{ts}.json"
            try:
                backup.write_text(self.path.read_text(encoding="utf-8"), encoding="utf-8")
                for old in sorted(self.backup_dir.glob("state-*.json"))[:-self.max_backups]:
                    old.unlink()
            except Exception as e:
                logger.warning(f"backup failed: {e}")
        self._write_atomic(state)


async def reconcile(state: BearHunterState, adapter) -> List[str]:
    warnings = []
    try:
        all_positions = await adapter.get_positions(active=True)
        actual = [p for p in all_positions if p.side == "short"]
    except Exception as e:
        state.mark_kill_switch(f"reconcile_api_error: {e}", source="auto")
        return [f"reconcile API error: {e}"]

    actual_ids = {p.position_id for p in actual}
    cached_ids = {p.position_id for p in state.open_positions}
    only_in_actual = actual_ids - cached_ids
    only_in_cache = cached_ids - actual_ids

    if only_in_actual:
        warnings.append(f"Unknown positions on exchange: {only_in_actual}")
        state.mark_kill_switch("unknown_positions_detected", source="auto")
    if only_in_cache:
        warnings.append(f"Positions closed on exchange (SL/TP?): {only_in_cache}")

    state.open_positions = actual
    state.last_reconciled_at = utcnow()
    return warnings
