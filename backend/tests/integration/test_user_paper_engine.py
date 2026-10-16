"""تست UserPaperEngine — subclass از PaperEngine.

پوشش: state lifecycle برای کاربر، subclass behavior، ارث‌بری متدها.
نیاز به DB لوکال.
"""

from __future__ import annotations

import uuid
from decimal import Decimal

import pytest
from sqlalchemy import delete

from app.domain.entities.candle import Candle
from app.infrastructure.db.models.user import User
from app.infrastructure.db.session import SessionLocal, engine
from app.infrastructure.paper_trading.user_engine import UserPaperEngine


class FakeExchange:
    """ExchangePort ساده — قیمت ثابت."""

    def __init__(self, price: float = 100.0):
        self.price = price

    async def get_candles(
        self,
        symbol: str,
        resolution: str,
        from_ts: int,
        to_ts: int,
    ) -> list[Candle]:
        p = Decimal(str(self.price))
        return [
            Candle(
                time=1000 + i * 3600,
                open=p, high=p, low=p, close=p,
                volume=Decimal("10"),
            )
            for i in range(200)
        ]


@pytest.fixture(autouse=True)
async def _dispose_engine_after_test():
    """engine.dispose() بعد از هر تست — جلوگیری از pool desync."""
    yield
    await engine.dispose()


@pytest.fixture
async def test_user():
    """user جدید می‌سازه، بعد پاک می‌کنه."""
    user_id = uuid.uuid4()
    email = f"test-eng-{user_id.hex[:8]}@example.local"

    async with SessionLocal() as session:
        user = User(
            id=user_id,
            email=email,
            password_hash="test-hash-not-real",
        )
        session.add(user)
        await session.commit()

    yield user_id

    async with SessionLocal() as session:
        await session.execute(delete(User).where(User.id == user_id))
        await session.commit()


@pytest.fixture
def exchange() -> FakeExchange:
    return FakeExchange(price=100.0)


def make_engine(
    test_user,
    exchange: FakeExchange,
    initial_capital: float = 3_000_000.0,
) -> UserPaperEngine:
    return UserPaperEngine(
        user_id=test_user,
        session_factory=SessionLocal,
        exchange=exchange,  # type: ignore[arg-type]
        bot_slug="mean_revert",
        symbols=["BTCTMN"],
        timeframe="1h",
        initial_capital=initial_capital,
        check_interval_sec=9999,
        position_size_pct=50.0,
        fee_pct=0.2,
    )


class TestFreshUser:
    async def test_new_user_engine_creates_state(
        self, test_user, exchange
    ) -> None:
        """user جدید → capital = initial_capital param."""
        engine = make_engine(test_user, exchange, initial_capital=3_000_000.0)
        await engine.ensure_state()

        assert engine.state.initial_capital == 3_000_000.0
        assert engine.state.capital == 3_000_000.0
        assert engine.state.equity == 3_000_000.0
        assert engine.state.is_running is False
        assert engine.state.open_positions == []

    async def test_custom_initial_capital(
        self, test_user, exchange
    ) -> None:
        """initial_capital دلخواه."""
        engine = make_engine(test_user, exchange, initial_capital=500_000.0)
        await engine.ensure_state()
        assert engine.state.capital == 500_000.0


class TestPersistence:
    async def test_state_persists_across_engines(
        self, test_user, exchange
    ) -> None:
        """engine دوم با همون user_id → state قبلی."""
        e1 = make_engine(test_user, exchange)
        await e1.ensure_state()
        e1.state.total_trades = 5
        e1.state.wins = 3
        e1.state.losses = 2
        await e1.repo.save(e1.state)

        e2 = make_engine(test_user, exchange)
        await e2.ensure_state()
        assert e2.state.total_trades == 5
        assert e2.state.wins == 3
        assert e2.state.losses == 2

    async def test_ensure_state_preserves_paper_meta_initial_capital(
        self, test_user, exchange
    ) -> None:
        """اگه paper_meta initial=1M داره، engine با param 3M override نکنه."""
        e1 = make_engine(test_user, exchange, initial_capital=1_000_000.0)
        await e1.ensure_state()
        assert e1.state.initial_capital == 1_000_000.0
        await e1.repo.save(e1.state)

        # engine دوم با param متفاوت
        e2 = make_engine(test_user, exchange, initial_capital=3_000_000.0)
        await e2.ensure_state()
        # باید 1M بمونه — از paper_meta
        assert e2.state.initial_capital == 1_000_000.0
        assert e2.state.capital == 1_000_000.0


class TestInheritance:
    async def test_execute_manual_order_inherited(
        self, test_user, exchange
    ) -> None:
        """execute_manual_order از پدر ارث می‌رسه و کار می‌کنه."""
        engine = make_engine(test_user, exchange)
        await engine.ensure_state()

        result = await engine.execute_manual_order(
            side="buy",
            symbol="BTCTMN",
            quantity=1.0,
            tp_pct=2.0,
            sl_pct=1.0,
        )
        assert result["status"] == "ok"
        assert len(engine.state.open_positions) == 1

        # persistence
        e2 = make_engine(test_user, exchange)
        await e2.ensure_state()
        assert len(e2.state.open_positions) == 1

    async def test_reset_persists(
        self, test_user, exchange
    ) -> None:
        """reset → engine جدید → state تمیز."""
        e1 = make_engine(test_user, exchange)
        await e1.ensure_state()
        await e1.execute_manual_order(side="buy", symbol="BTCTMN", quantity=1.0)
        await e1.reset()

        e2 = make_engine(test_user, exchange)
        await e2.ensure_state()
        assert e2.state.open_positions == []
        assert e2.state.capital == 3_000_000.0
        assert e2.state.total_trades == 0
