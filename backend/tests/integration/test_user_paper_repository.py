"""تست UserPaperRepository — پیاده‌سازی DB-backed.

نیاز به DB لوکال (wallex_postgres_dev) داره.
هر تست user جدید می‌سازه، بعد پاک می‌کنه.
"""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import delete

from app.infrastructure.db.models.user import User
from app.infrastructure.db.session import SessionLocal, engine
from app.infrastructure.paper_trading.state import PaperState
from app.infrastructure.paper_trading.user_repository import UserPaperRepository


@pytest.fixture(autouse=True)
async def _dispose_engine_after_test():
    """بعد از هر تست، engine.dispose() — pool رو ریست کن.

    چرا: pytest-asyncio با function-scoped loop، هر تست یه loop جدا داره.
    اگه pool اتصالات از loop قبلی نگه داره، RuntimeError می‌ده.
    """
    yield
    await engine.dispose()


@pytest.fixture
async def test_user():
    """یه user جدید می‌سازه، بعد پاک می‌کنه."""
    user_id = uuid.uuid4()
    email = f"test-{user_id.hex[:8]}@example.local"

    async with SessionLocal() as session:
        user = User(
            id=user_id,
            email=email,
            password_hash="test-hash-not-real",
        )
        session.add(user)
        await session.commit()

    yield user_id

    # cleanup
    async with SessionLocal() as session:
        await session.execute(delete(User).where(User.id == user_id))
        await session.commit()


@pytest.fixture
def repo(test_user):
    return UserPaperRepository(user_id=test_user, session_factory=SessionLocal)


class TestExists:
    async def test_new_user_no_state(self, repo) -> None:
        """user جدید → exists() = False."""
        assert await repo.exists() is False

    async def test_after_save_exists_true(self, repo) -> None:
        """بعد از save → exists() = True."""
        state = PaperState()
        state.capital = 2_500_000.0
        state.total_trades = 5
        await repo.save(state)
        assert await repo.exists() is True


class TestLoadFallback:
    async def test_load_empty_returns_defaults(self, repo) -> None:
        """user جدید با paper_meta خالی → defaults."""
        state = await repo.load()
        # fallback: initial_capital = capital_total (3M)
        assert state.initial_capital == 3_000_000.0
        assert state.capital == 3_000_000.0
        assert state.is_running is False
        assert state.open_positions == []


class TestRoundtrip:
    async def test_full_state_roundtrip(self, repo) -> None:
        """save کامل → load → همه‌ی ۲۱ فیلد یکسان."""
        original = PaperState()
        original.initial_capital = 1_000_000.0
        original.capital = 950_000.0
        original.equity = 980_000.0
        original.peak_capital = 1_050_000.0
        original.peak_equity = 1_080_000.0
        original.max_drawdown_pct = 3.5
        original.total_trades = 10
        original.wins = 6
        original.losses = 4
        original.total_pnl = -20_000.0
        original.total_pnl_pct = -2.0
        original.win_rate = 60.0
        original.is_running = True
        original.started_at = 1234567890
        original.last_check_at = 1234567999
        original.check_count = 42
        original.open_positions = [
            {"symbol": "BTCTMN", "side": "BUY", "entry_price": 100.0, "quantity": 1.5}
        ]
        original.recent_trades = [
            {"symbol": "ETHTMN", "pnl": 5000.0, "exit_reason": "take_profit"}
        ]
        original.equity_curve = [{"time": 1000, "capital": 1_000_000.0}]
        original.events = [{"time": 1000, "kind": "start"}]
        original.radar = [{"symbol": "BTCTMN", "passed": 3, "total": 5}]

        await repo.save(original)
        loaded = await repo.load()

        assert loaded.initial_capital == 1_000_000.0
        assert loaded.capital == 950_000.0
        assert loaded.equity == 980_000.0
        assert loaded.peak_capital == 1_050_000.0
        assert loaded.peak_equity == 1_080_000.0
        assert loaded.max_drawdown_pct == 3.5
        assert loaded.total_trades == 10
        assert loaded.wins == 6
        assert loaded.losses == 4
        assert loaded.total_pnl == -20_000.0
        assert loaded.total_pnl_pct == -2.0
        assert loaded.win_rate == 60.0
        assert loaded.is_running is True
        assert loaded.started_at == 1234567890
        assert loaded.last_check_at == 1234567999
        assert loaded.check_count == 42
        assert len(loaded.open_positions) == 1
        assert loaded.open_positions[0]["symbol"] == "BTCTMN"
        assert len(loaded.recent_trades) == 1
        assert loaded.equity_curve == [{"time": 1000, "capital": 1_000_000.0}]
        assert loaded.events == [{"time": 1000, "kind": "start"}]
        assert loaded.radar == [{"symbol": "BTCTMN", "passed": 3, "total": 5}]

    async def test_save_twice_updates(self, repo) -> None:
        """save دوباره → state آپدیت می‌شه."""
        s1 = PaperState()
        s1.capital = 1_000_000.0
        s1.total_trades = 3
        await repo.save(s1)

        s2 = PaperState()
        s2.capital = 900_000.0
        s2.total_trades = 7
        await repo.save(s2)

        loaded = await repo.load()
        assert loaded.capital == 900_000.0
        assert loaded.total_trades == 7


class TestSyncGuarantee:
    async def test_capital_total_unchanged(self, repo, test_user) -> None:
        """capital_total دست‌نخورده می‌مونه حتی با save."""
        state = PaperState()
        state.capital = 500_000.0  # capital_available
        state.initial_capital = 3_000_000.0
        await repo.save(state)

        async with SessionLocal() as session:
            user = await session.get(User, test_user)
            # capital_total = investment کل → 3M (پیش‌فرض)
            assert float(user.capital_total) == 3_000_000.0
            # capital_available = نقد → 500k
            assert float(user.capital_available) == 500_000.0
