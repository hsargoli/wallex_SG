"""FeedbackTrail — append-only JSONL for user feedback on Copilot decisions (ADR-0043)."""
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

_BACKEND = Path(__file__).resolve().parent.parent.parent.parent.parent
DEFAULT_DIR = _BACKEND / "data" / "sarv_router" / "users"

@dataclass
class FeedbackEntry:
    tick_id: str
    action: str
    user_choice: str  # "accept" | "reject"
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return asdict(self)

class FeedbackTrail:
    """Append-only JSONL per user. Fail-safe (never raises on write/read)."""
    def __init__(self, base_dir: Path | None = None):
        self.base_dir = Path(base_dir) if base_dir else DEFAULT_DIR
        try:
            self.base_dir.mkdir(parents=True, exist_ok=True)
        except OSError:
            pass

    def _path(self, user_id: str) -> Path:
        return self.base_dir / f"{user_id}.feedback.jsonl"

    def write(self, user_id: str, entry: FeedbackEntry) -> None:
        try:
            with open(self._path(user_id), "a", encoding="utf-8") as f:
                f.write(json.dumps(entry.to_dict(), ensure_ascii=False) + "\n")
        except OSError:
            pass

    def read_all(self, user_id: str) -> list[dict]:
        p = self._path(user_id)
        if not p.exists():
            return []
        entries = []
        try:
            with open(p, encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        entries.append(json.loads(line))
        except (OSError, json.JSONDecodeError):
            return []
        return entries
