"""Gate — shared flag for cross-system entry control (zero coupling).

SarvRouter writes; nooaah (and future sarvban) reads.
Fail-safe: missing or corrupted file → allow_new_entries=True.
"""
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

_BACKEND = Path(__file__).resolve().parent.parent.parent.parent.parent
DEFAULT_PATH = _BACKEND / "data" / "sarv_router" / "gate.json"


@dataclass
class GateState:
    allow_new_entries: bool = True
    regime: str = "unknown"
    updated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


def write_gate(
    allow_new_entries: bool,
    regime: str,
    path: Path | None = None,
) -> None:
    """Write gate state. Creates parent dirs if needed. Silent on error."""
    p = Path(path) if path else DEFAULT_PATH
    state = GateState(allow_new_entries=allow_new_entries, regime=regime)
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(asdict(state), ensure_ascii=False, indent=2))
    except OSError:
        pass  # fail-safe: never crash on gate write


def read_gate(path: Path | None = None) -> GateState:
    """Read gate state. Fail-safe: returns default (allow=True) on any error."""
    p = Path(path) if path else DEFAULT_PATH
    if not p.exists():
        return GateState()
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return GateState()
    valid = GateState.__dataclass_fields__.keys()
    filtered = {k: v for k, v in data.items() if k in valid}
    try:
        return GateState(**filtered)
    except (TypeError, ValueError):
        return GateState()
