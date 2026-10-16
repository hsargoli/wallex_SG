"""Paper Trading Repository — ذخیره/بازیابی state (async facade)."""

import asyncio
import json
from pathlib import Path

from app.infrastructure.paper_trading.state import PaperState

STATE_DIR = Path("data/paper_v3")
STATE_FILE = STATE_DIR / "state.json"


class PaperRepository:
    """Repository state فایلـی — async facade روی I/O sync."""

    def __init__(self, state_dir: Path = STATE_DIR):
        self.state_dir = state_dir
        self.state_file = state_dir / "state.json"
        self.state_dir.mkdir(parents=True, exist_ok=True)

    async def exists(self) -> bool:
        """آیا فایل state وجود دارد؟"""
        return await asyncio.to_thread(self.state_file.exists)

    async def load(self) -> PaperState:
        """بارگذاری state — async wrapper."""
        return await asyncio.to_thread(self._load_sync)

    async def save(self, state: PaperState) -> None:
        """ذخیره state — async wrapper."""
        await asyncio.to_thread(self._save_sync, state)

    # ── sync internals (اجرا در thread جدا) ──

    def _load_sync(self) -> PaperState:
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

    def _save_sync(self, state: PaperState) -> None:
        self.state_file.write_text(
            json.dumps(state.to_dict(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
