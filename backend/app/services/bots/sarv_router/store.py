"""SarvStore — per-user JSON state persistence for SarvRouter."""
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

_BACKEND = Path(__file__).resolve().parent.parent.parent.parent.parent
DEFAULT_DIR = _BACKEND / "data" / "sarv_router" / "users"


@dataclass
class SarvState:
    """Per-user SarvRouter state."""
    total_capital: float = 1_000_000.0
    current_regime: str = "unknown"
    active_bots: list[str] = field(default_factory=list)
    allocations: dict[str, float] = field(default_factory=dict)
    cash: float = 1_000_000.0
    last_switch_idx: int | None = None
    regime_since_idx: int | None = None
    daily_pnl_pct: float = 0.0
    daily_reset_day: str = ""
    kill_switch_manual: bool = False
    kill_switch_auto: bool = False


class SarvStore:
    """Save/load SarvState per user. Fail-safe (corrupted → default)."""

    def __init__(self, base_dir: Path | None = None):
        self.base_dir = Path(base_dir) if base_dir else DEFAULT_DIR
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _state_path(self, user_id: str) -> Path:
        return self.base_dir / f"{user_id}.json"

    def audit_path(self, user_id: str) -> Path:
        return self.base_dir / f"{user_id}.audit.jsonl"

    def save(self, user_id: str, state: SarvState) -> None:
        path = self._state_path(user_id)
        data: dict[str, Any] = asdict(state)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load(self, user_id: str) -> SarvState:
        path = self._state_path(user_id)
        if not path.exists():
            return SarvState()
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            return SarvState()  # fail-safe

        valid = SarvState.__dataclass_fields__.keys()
        filtered = {k: v for k, v in data.items() if k in valid}
        try:
            return SarvState(**filtered)
        except (TypeError, ValueError):
            return SarvState()  # fail-safe on bad types
