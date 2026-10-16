"""UserPaperRepository — ذخیره/بازیابی PaperState برای کاربر لاگین‌شده.

پیاده‌سازی PaperRepositoryProtocol روی PostgreSQL.

نگاشت:
- capital_available ← state.capital (نقد)
- capital_total ← دست‌نخورده (سرمایه‌ی کل — ممکنه با سود/زیان تغییر کنه)
- open_positions, closed_trades, equity_curve ← مستقیم
- total_trades, wins, losses ← مستقیم
- paper_meta (JSONB) ← ۱۰ فیلد بی‌خونه:
  initial_capital, equity, peak_capital, peak_equity, max_drawdown_pct,
  total_pnl, total_pnl_pct, win_rate, is_running, started_at,
  last_check_at, check_count, events, radar

⚠️ sync guarantee: همه‌ی تغییرات state از طریق این repo انجام می‌شه.
   هیچ‌جا مستقیم session.execute(update(User)) نزن — paper_meta desync می‌شه.

منابع: ADR 0015 + Addendum 1
"""

from __future__ import annotations

import uuid
from typing import Any

from app.infrastructure.db.models.user import User
from app.infrastructure.paper_trading.state import PaperState


class UserPaperRepository:
    """Repository PaperState روی کاربر لاگین‌شده."""

    def __init__(self, user_id: uuid.UUID, session_factory: Any):
        """
        Args:
            user_id: UUID کاربر
            session_factory: async_sessionmaker (مثل SessionLocal)
        """
        self.user_id = user_id
        self.session_factory = session_factory

    async def exists(self) -> bool:
        """آیا کاربر state قبلاً داشته؟

        معیار: paper_meta غیرخالی یا total_trades > 0.
        """
        async with self.session_factory() as session:
            user = await session.get(User, self.user_id)
            if user is None:
                return False
            meta = user.paper_meta or {}
            return bool(meta) or user.total_trades > 0

    async def load(self) -> PaperState:
        """بارگذاری state کاربر. اگه کاربر نبود، PaperState خالی."""
        async with self.session_factory() as session:
            user = await session.get(User, self.user_id)
            if user is None:
                return PaperState()
            return self._user_to_state(user)

    async def save(self, state: PaperState) -> None:
        """ذخیره state. هر save = یک تراکنش کامل."""
        async with self.session_factory() as session:
            user = await session.get(User, self.user_id)
            if user is None:
                raise ValueError(f"User {self.user_id} not found")
            self._apply_state_to_user(user, state)
            await session.commit()

    # ═══════════════════════════════════════════
    # Mapping helpers
    # ═══════════════════════════════════════════

    @staticmethod
    def _user_to_state(user: User) -> PaperState:
        """تبدیل User → PaperState."""
        state = PaperState()

        # ستون‌های مستقیم User
        state.capital = float(user.capital_available)
        state.open_positions = list(user.open_positions or [])
        state.recent_trades = list(user.closed_trades or [])[:50]
        state.equity_curve = list(user.equity_curve or [])
        state.total_trades = user.total_trades
        state.wins = user.wins
        state.losses = user.losses

        # paper_meta (۱۰ فیلد بی‌خونه)
        meta = user.paper_meta or {}
        fallback_capital = float(user.capital_total)

        state.initial_capital = float(meta.get("initial_capital", fallback_capital))
        state.equity = float(meta.get("equity", state.capital))
        state.peak_capital = float(meta.get("peak_capital", state.capital))
        state.peak_equity = float(meta.get("peak_equity", state.equity))
        state.max_drawdown_pct = float(meta.get("max_drawdown_pct", 0.0))
        state.total_pnl = float(meta.get("total_pnl", 0.0))
        state.total_pnl_pct = float(meta.get("total_pnl_pct", 0.0))
        state.win_rate = float(meta.get("win_rate", 0.0))
        state.is_running = bool(meta.get("is_running", False))
        state.started_at = int(meta.get("started_at", 0))
        state.last_check_at = int(meta.get("last_check_at", 0))
        state.check_count = int(meta.get("check_count", 0))
        state.events = list(meta.get("events", []))
        state.radar = list(meta.get("radar", []))

        return state

    @staticmethod
    def _apply_state_to_user(user: User, state: PaperState) -> None:
        """اعمال PaperState روی User (ستون‌ها + paper_meta)."""
        # ستون‌های مستقیم
        user.capital_available = state.capital
        user.open_positions = state.open_positions
        user.closed_trades = state.recent_trades
        user.equity_curve = state.equity_curve
        user.total_trades = state.total_trades
        user.wins = state.wins
        user.losses = state.losses

        # capital_total دست‌نخورده — investment کل

        # paper_meta — ۱۰ فیلد بی‌خونه
        user.paper_meta = {
            "initial_capital": state.initial_capital,
            "equity": state.equity,
            "peak_capital": state.peak_capital,
            "peak_equity": state.peak_equity,
            "max_drawdown_pct": state.max_drawdown_pct,
            "total_pnl": state.total_pnl,
            "total_pnl_pct": state.total_pnl_pct,
            "win_rate": state.win_rate,
            "is_running": state.is_running,
            "started_at": state.started_at,
            "last_check_at": state.last_check_at,
            "check_count": state.check_count,
            "events": state.events,
            "radar": state.radar,
        }
