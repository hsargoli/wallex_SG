"""Characterization tests: scalp_master async runtime (M2, M5, M6).

Monkeypatches GetCandlesUseCase and evaluate_entry — no real exchange.
Zero production changes.
"""
from decimal import Decimal

import pytest

import app.application.use_cases.get_candles as gc_mod
import app.services.bots.scalp_master.bot as bot_mod
from app.domain.entities.candle import Candle
from app.services.bots.base import BotStatus
from app.services.bots.scalp_master.bot import ScalpMasterBot


def _candle(i: int, base: float = 100.0) -> Candle:
    p = Decimal(str(base + (i % 5) - 2))
    return Candle(
        time=1000 + i,
        open=p,
        high=p + Decimal("1"),
        low=p - Decimal("1"),
        close=p,
        volume=Decimal("10"),
    )


def _patch_uc(monkeypatch, candles=None, raises=None):
    """Replace GetCandlesUseCase inside _check_symbols (lazy-imported)."""
    class _FakeUC:
        def __init__(self, exchange):
            pass

        async def execute(self, symbol, timeframe, limit):
            if raises is not None:
                raise raises
            return list(candles or [])

    monkeypatch.setattr(gc_mod, "GetCandlesUseCase", _FakeUC)


class TestBotRuntime:
    """M2, M5, M6 — start/stop + _check_symbols flow."""

    @pytest.mark.asyncio
    async def test_start_stop_lifecycle(self, monkeypatch):
        """M2: start → running; second start → already_running; stop → stopped."""
        _patch_uc(monkeypatch, candles=[])  # empty → no signal work

        bot = ScalpMasterBot()
        exchange = object()  # unused (UC patched)

        r1 = await bot.start(exchange)
        assert r1["status"] == "started"
        assert bot.state.is_running is True
        assert bot.status == BotStatus.RUNNING

        r2 = await bot.start(exchange)
        assert r2["status"] == "already_running"

        r3 = await bot.stop()
        assert r3["status"] == "stopped"
        assert bot.state.is_running is False
        assert bot.status == BotStatus.STOPPED

    @pytest.mark.asyncio
    async def test_check_symbols_produces_signal(self, monkeypatch):
        """M5: when evaluate_entry yields a signal, it must be logged."""
        candles = [_candle(i) for i in range(70)]  # > warmup(60)
        _patch_uc(monkeypatch, candles=candles)

        class _Sig:
            should_trade = True
            action = "buy"
            entry_price = 100.0
            take_profit = 110.0
            stop_loss = 95.0
            reason = "test-signal"
            drop_pct = 3.0
            rsi = 35.0

        monkeypatch.setattr(bot_mod, "evaluate_entry", lambda c, cfg: _Sig())

        bot = ScalpMasterBot()
        bot.config.symbols = ["TESTSYMBOL"]

        await bot._check_symbols(object())

        assert bot.state.check_count == 1
        assert len(bot.state.recent_signals) == 1
        sig = bot.state.recent_signals[0]
        assert sig["symbol"] == "TESTSYMBOL"
        assert sig["action"] == "buy"
        assert sig["entry"] == 100.0

    @pytest.mark.asyncio
    async def test_check_symbols_handles_exchange_error(self, monkeypatch):
        """M6: exchange error must not crash _check_symbols."""
        _patch_uc(monkeypatch, raises=RuntimeError("boom"))

        bot = ScalpMasterBot()
        bot.config.symbols = ["X", "Y"]

        await bot._check_symbols(object())  # must not raise

        assert bot.state.check_count == 1
        assert bot.state.recent_signals == []
