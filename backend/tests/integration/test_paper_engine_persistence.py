"""Integration test برای PaperEngine — safety net برای refactor فاز ۱۷.۷.۱.

هدف: تضمین اینکه refactor async (۱۷.۷.۱) رفتار فعلی رو حفظ می‌کنه.
پوشش: persistence, load/save, state transitions, manual order.

این تست عمداً منطق trading رو تست نمی‌کنه — فقط persistence و
state lifecycle رو قفل می‌کنه، چون refactor ۱۷.۷.۱ قراره دقیقاً همین‌ها
رو دست بزنه (sync → async).
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import pytest

from app.domain.entities.candle import Candle
from app.infrastructure.paper_trading.engine import PaperEngine
from app.infrastructure.paper_trading.repository import PaperRepository
from app.infrastructure.paper_trading.state import PaperState


# ──────────────────────────────────────────────
# Fake Exchange — قیمت ثابت، بدون سیگنال
# ──────────────────────────────────────────────

class FakeExchange:
    """ExchangePort ساده — قیمت ثابت، کندل‌های flat."""

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
        # ۲۰۰ کندل flat — کافی برای هر bot، بدون trigger
        return [
            Candle(
                time=1000 + i * 3600,
                open=p,
                high=p,
                low=p,
                close=p,
                volume=Decimal("10"),
            )
            for i in range(200)
        ]


# ──────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────

@pytest.fixture
def state_dir(tmp_path: Path) -> Path:
    """مسیر ایزوله برای state هر تست."""
    return tmp_path / "paper_state"


@pytest.fixture
def exchange() -> FakeExchange:
    return FakeExchange(price=100.0)


def make_engine(
    exchange: FakeExchange,
    state_dir: Path,
    initial_capital: float = 100_000.0,
) -> PaperEngine:
    """ساخت engine با تنظیمات تست."""
    return PaperEngine(
        exchange=exchange,  # type: ignore[arg-type]
        bot_slug="mean_revert",
        symbols=["BTCTMN"],
        timeframe="1h",
        initial_capital=initial_capital,
        check_interval_sec=9999,  # loop عملاً اجرا نمی‌شه
        position_size_pct=50.0,
        fee_pct=0.2,
        state_dir=state_dir,
    )


# ──────────────────────────────────────────────
# تست‌ها — State lifecycle
# ──────────────────────────────────────────────

class TestFreshState:
    def test_new_engine_creates_fresh_state(
        self, exchange: FakeExchange, state_dir: Path
    ) -> None:
        """engine جدید روی state_dir خالی → capital = initial_capital."""
        engine = make_engine(exchange, state_dir, initial_capital=100_000.0)

        assert engine.state.capital == 100_000.0
        assert engine.state.initial_capital == 100_000.0
        assert engine.state.equity == 100_000.0
        assert engine.state.is_running is False
        assert engine.state.open_positions == []
        assert engine.state.total_trades == 0

    def test_initial_capital_is_respected(
        self, exchange: FakeExchange, state_dir: Path
    ) -> None:
        """initial_capital دلخواه اعمال می‌شه."""
        engine = make_engine(exchange, state_dir, initial_capital=3_000_000.0)
        assert engine.state.capital == 3_000_000.0


class TestPersistence:
    def test_existing_state_is_loaded(
        self, exchange: FakeExchange, state_dir: Path
    ) -> None:
        """engine دوم با همون state_dir → state قبلی رو لود می‌کنه."""
        # engine اول: چند تا تغییر
        engine1 = make_engine(exchange, state_dir, initial_capital=100_000.0)
        engine1.state.total_trades = 7
        engine1.state.wins = 5
        engine1.state.losses = 2
        engine1.repo.save(engine1.state)

        # engine دوم: باید state قبلی رو ببینه
        engine2 = make_engine(exchange, state_dir, initial_capital=100_000.0)
        assert engine2.state.total_trades == 7
        assert engine2.state.wins == 5
        assert engine2.state.losses == 2

    def test_reset_persists_across_engines(
        self, exchange: FakeExchange, state_dir: Path
    ) -> None:
        """reset → engine جدید → state تمیز."""
        engine1 = make_engine(exchange, state_dir, initial_capital=100_000.0)
        engine1.state.total_trades = 5
        engine1.repo.save(engine1.state)

        engine1.reset()

        engine2 = make_engine(exchange, state_dir, initial_capital=100_000.0)
        assert engine2.state.total_trades == 0
        assert engine2.state.capital == 100_000.0
        assert engine2.state.open_positions == []

    def test_manual_order_persists(
        self, exchange: FakeExchange, state_dir: Path
    ) -> None:
        """execute_manual_order → engine جدید → پوزیشن هنوز هست."""
        import asyncio

        engine1 = make_engine(exchange, state_dir, initial_capital=100_000.0)

        result = asyncio.run(
            engine1.execute_manual_order(
                side="buy",
                symbol="BTCTMN",
                quantity=1.0,
                tp_pct=2.0,
                sl_pct=1.0,
            )
        )
        assert result["status"] == "ok"
        assert len(engine1.state.open_positions) == 1

        # engine جدید
        engine2 = make_engine(exchange, state_dir, initial_capital=100_000.0)
        assert len(engine2.state.open_positions) == 1
        assert engine2.state.open_positions[0]["symbol"] == "BTCTMN"


class TestReset:
    def test_reset_clears_positions(
        self, exchange: FakeExchange, state_dir: Path
    ) -> None:
        """reset → open_positions خالی، capital برمی‌گرده."""
        import asyncio

        engine = make_engine(exchange, state_dir, initial_capital=100_000.0)
        asyncio.run(
            engine.execute_manual_order(
                side="buy", symbol="BTCTMN", quantity=1.0,
            )
        )
        assert len(engine.state.open_positions) == 1

        engine.reset()

        assert engine.state.open_positions == []
        assert engine.state.capital == 100_000.0
        assert engine.state.equity == 100_000.0
        assert engine.state.total_trades == 0

    def test_reset_preserves_initial_capital(
        self, exchange: FakeExchange, state_dir: Path
    ) -> None:
        """reset → initial_capital حفظ می‌شه."""
        engine = make_engine(exchange, state_dir, initial_capital=3_000_000.0)
        engine.reset()
        assert engine.state.initial_capital == 3_000_000.0
        assert engine.state.capital == 3_000_000.0


class TestRepositoryRoundtrip:
    def test_repo_save_load_roundtrip(self, state_dir: Path) -> None:
        """PaperRepository: save → load → مساوی."""
        repo = PaperRepository(state_dir=state_dir)

        state = PaperState()
        state.capital = 12_345.67
        state.total_trades = 42
        state.wins = 30
        state.losses = 12
        state.open_positions = [
            {"symbol": "BTCTMN", "side": "BUY", "entry_price": 100.0, "quantity": 1.0}
        ]

        repo.save(state)
        loaded = repo.load()

        assert loaded.capital == 12_345.67
        assert loaded.total_trades == 42
        assert loaded.wins == 30
        assert loaded.losses == 12
        assert len(loaded.open_positions) == 1
        assert loaded.open_positions[0]["symbol"] == "BTCTMN"

    def test_repo_load_missing_file_returns_empty(self, state_dir: Path) -> None:
        """load روی فایل ناموجود → PaperState خالی."""
        repo = PaperRepository(state_dir=state_dir)
        state = repo.load()
        assert state.capital == 1000.0  # default PaperState
        assert state.total_trades == 0

    def test_repo_state_file_exists_check(self, state_dir: Path) -> None:
        """state_file.exists() قبل و بعد از save."""
        repo = PaperRepository(state_dir=state_dir)
        assert repo.state_file.exists() is False
        repo.save(PaperState())
        assert repo.state_file.exists() is True
