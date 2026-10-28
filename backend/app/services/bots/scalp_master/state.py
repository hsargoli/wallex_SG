"""ScalpState — per-user state for scalp_master (Phase B2).

Extracted from bot.py to break circular import between bot.py and store.py.
"""
import asyncio
from dataclasses import dataclass, field

from app.domain.entities.paper_position import PaperPosition


@dataclass
class ScalpState:
    """State اسکالپ‌مستر (per-user)."""

    is_running: bool = False
    paper_mode: bool = True
    started_at: int = 0
    last_check_at: int = 0
    check_count: int = 0
    recent_signals: list[dict] = field(default_factory=list)
    open_positions: list[PaperPosition] = field(default_factory=list)
    capital: float = 300_000.0
    _task: asyncio.Task | None = None
