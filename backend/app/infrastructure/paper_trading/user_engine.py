"""UserPaperEngine — PaperEngine برای کاربر لاگین‌شده.

subclass از PaperEngine. تنها تفاوت‌ها:
- repo از نوع UserPaperRepository (DB-backed) به‌جای PaperRepository (فایلـی)
- initial_capital از paper_meta میاد، نه از param (override نمی‌شه)

همه‌ی منطق trading (check, entries, exits, manual_order, close_position)
بدون تغییر ارث می‌رسه.

منابع: ADR 0015 + Addendum 1
"""

from __future__ import annotations

import uuid
from typing import Any

from app.domain.ports.exchange import ExchangePort
from app.infrastructure.paper_trading.engine import PaperEngine
from app.infrastructure.paper_trading.user_repository import UserPaperRepository


class UserPaperEngine(PaperEngine):
    """موتور Paper Trading برای کاربر لاگین‌شده."""

    def __init__(
        self,
        user_id: uuid.UUID,
        session_factory: Any,
        exchange: ExchangePort,
        bot_slug: str,
        symbols: list[str],
        timeframe: str = "1h",
        initial_capital: float = 3_000_000.0,
        check_interval_sec: int = 180,
        position_size_pct: float = 50.0,
        fee_pct: float = 0.2,
    ):
        repo = UserPaperRepository(
            user_id=user_id,
            session_factory=session_factory,
        )
        super().__init__(
            exchange=exchange,
            bot_slug=bot_slug,
            symbols=symbols,
            timeframe=timeframe,
            initial_capital=initial_capital,
            check_interval_sec=check_interval_sec,
            position_size_pct=position_size_pct,
            fee_pct=fee_pct,
            state_dir=None,
            repo=repo,
        )
        self.user_id = user_id

    async def ensure_state(self) -> None:
        """ensure_state مخصوص UserPaperEngine.

        تفاوت با پدر: اگه state وجود داره، initial_capital رو
        با مقدار param override نمی‌کنه — چون منبع حقیقت paper_meta است.
        برای کاربر جدید (state خالی)، از param استفاده می‌کنه.
        """
        if self._state_initialized:
            return
        exists = await self.repo.exists()
        self.state = await self.repo.load()
        if not exists:
            self.state.initial_capital = self._initial_capital
            self.state.capital = self._initial_capital
            self.state.equity = self._initial_capital
            self.state.peak_capital = self._initial_capital
            self.state.peak_equity = self._initial_capital
        # اگه exists: مقادیر paper_meta دست‌نخورده می‌مونن
        self._state_initialized = True
