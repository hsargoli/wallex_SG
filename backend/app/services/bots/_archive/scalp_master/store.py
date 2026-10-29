"""ScalpStore — save/load ScalpState per user (JSON)."""
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict
from app.services.bots.scalp_master.state import ScalpState
from app.services.bots.scalp_master.paths import user_state_path, USERS_DIR

class ScalpStore:
    def __init__(self, base_dir: Path | None = None):
        self.base_dir = base_dir or USERS_DIR
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _path(self, user_id: str) -> Path:
        return self.base_dir / f"{user_id}.json"

    def save(self, user_id: str, state: ScalpState) -> None:
        path = self._path(user_id)
        # Temporarily clear _task (asyncio.Task is not deepcopy-able by asdict)
        task = state._task
        state._task = None
        try:
            d = asdict(state)
        finally:
            state._task = task
        with open(path, "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False, indent=2)

    def load(self, user_id: str) -> ScalpState:
        path = self._path(user_id)
        if not path.exists():
            return ScalpState()
        
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # Filter to only known dataclass fields (backward compat)
        valid_fields = ScalpState.__dataclass_fields__.keys()
        filtered = {k: v for k, v in data.items() if k in valid_fields}
        return ScalpState(**filtered)
