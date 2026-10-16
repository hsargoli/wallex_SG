"""PaperRepositoryProtocol — قرارداد انتزاعی برای هر repository paper.

هدف: یک interface یکسان برای پیاده‌سازی‌های مختلف:
- PaperRepository (فایلـی) — data/paper_v3/state.json
- UserPaperRepository (DB) — ستون‌های users.open_positions/closed_trades/...

همه‌ی متدها async هستن — حتی اگه پیاده‌سازی sync باشه، با asyncio.to_thread
پوشش داده می‌شه.
"""

from typing import Protocol, runtime_checkable

from app.infrastructure.paper_trading.state import PaperState


@runtime_checkable
class PaperRepositoryProtocol(Protocol):
    """قرارداد انتزاعی برای ذخیره/بازیابی PaperState."""

    async def exists(self) -> bool:
        """آیا state قبلاً ذخیره شده؟"""
        ...

    async def load(self) -> PaperState:
        """بارگذاری state. اگه نبود، PaperState خالی برمی‌گردونه."""
        ...

    async def save(self, state: PaperState) -> None:
        """ذخیره state."""
        ...
