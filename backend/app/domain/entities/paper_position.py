"""PaperPosition — پوزیشن باز در Paper Trading."""

from dataclasses import dataclass


@dataclass(slots=True)
class PaperPosition:
    """پوزیشن باز."""

    symbol: str
    side: str  # "BUY"
    entry_price: float
    quantity: float
    tp: float
    sl: float
    entry_time: int
    entry_idx: int
    reason: str
    bot_slug: str
