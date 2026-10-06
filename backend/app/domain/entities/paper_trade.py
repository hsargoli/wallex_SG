"""PaperTrade — ترید بسته‌شده در Paper Trading."""

from dataclasses import dataclass


@dataclass(slots=True)
class PaperTrade:
    """ترید بسته‌شده."""

    symbol: str
    side: str
    entry_time: int
    exit_time: int
    entry_price: float
    exit_price: float
    quantity: float
    pnl: float
    pnl_pct: float
    exit_reason: str
    duration_minutes: int
    bot_slug: str
