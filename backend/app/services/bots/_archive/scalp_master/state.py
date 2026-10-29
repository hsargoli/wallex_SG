"""ScalpState — per-user state for scalp_master (Phase B2).

Extracted from bot.py to break circular import between bot.py and store.py.
"""
import asyncio
from dataclasses import dataclass, field

from app.domain.entities.paper_position import PaperPosition


@dataclass
class ClosedTrade:
    """یک ترید بسته‌شده (paper)."""

    symbol: str
    side: str
    entry_price: float
    exit_price: float
    quantity: float
    tp: float
    sl: float
    entry_time: int
    exit_time: int
    pnl_net: float
    exit_reason: str  # "take_profit" | "stop_loss" | "timeout"
    bot_slug: str


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
    closed_trades: list[ClosedTrade] = field(default_factory=list)
    watchlist: dict[str, dict] = field(default_factory=dict)
    capital: float = 300_000.0
    _task: asyncio.Task | None = None
