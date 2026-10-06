"""Paper Trading Repository — ذخیره/بازیابی state."""

import json
from pathlib import Path

from app.infrastructure.paper_trading.state import PaperState

STATE_DIR = Path("data/paper_v3")
STATE_FILE = STATE_DIR / "state.json"


class PaperRepository:
    """Repository state."""

    def __init__(self, state_dir: Path = STATE_DIR):
        self.state_dir = state_dir
        self.state_file = state_dir / "state.json"
        self.state_dir.mkdir(parents=True, exist_ok=True)

    def load(self) -> PaperState:
        """بارگذاری state."""
        if not self.state_file.exists():
            return PaperState()
        try:
            data = json.loads(self.state_file.read_text(encoding="utf-8"))
            state = PaperState()
            for key, value in data.items():
                if hasattr(state, key):
                    setattr(state, key, value)
            return state
        except Exception:
            return PaperState()

    def save(self, state: PaperState) -> None:
        """ذخیره state."""
        self.state_file.write_text(
            json.dumps(state.to_dict(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
