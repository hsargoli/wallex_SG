"""AuditTrail — append-only WAL for SarvRouter decisions (per-user)."""
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

_BACKEND = Path(__file__).resolve().parent.parent.parent.parent.parent
DEFAULT_DIR = _BACKEND / "data" / "sarv_router" / "users"


@dataclass
class AuditEntry:
    type: str  # "tick" | "switch" | "kill_switch" | "error"
    from_regime: str
    to_regime: str
    from_bots: list[str]
    to_bots: list[str]
    reason: str
    allocations: dict[str, float]
    cash: float
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class AuditTrail:
    """Append-only JSONL per user. Fail-safe (never raises on write)."""

    def __init__(self, base_dir: Path | None = None):
        self.base_dir = Path(base_dir) if base_dir else DEFAULT_DIR
        try:
            self.base_dir.mkdir(parents=True, exist_ok=True)
        except OSError:
            pass  # fail-safe: if can't create dir, log() will also fail-safe

    def log(self, user_id: str, entry: AuditEntry) -> None:
        path = self.base_dir / f"{user_id}.audit.jsonl"
        line = json.dumps(asdict(entry), ensure_ascii=False, default=str) + "\n"
        try:
            with open(path, "a", encoding="utf-8") as f:
                f.write(line)
        except OSError:
            pass  # fail-safe: never crash on log error
