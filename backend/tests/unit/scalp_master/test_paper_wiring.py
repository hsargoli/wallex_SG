"""P2c: _check_symbols must wire _paper_entry in paper mode."""

import pytest

import app.application.use_cases.get_candles as gc_mod
import app.services.bots.scalp_master.bot as bot_mod
from app.services.bots.scalp_master.bot import ScalpMasterBot


class _Sig:
    should_trade = True
    action = "buy"
    entry_price = 100.0
    take_profit = 110.0
    stop_loss = 95.0
    reason = "wire-signal"
    drop_pct = 3.0
    rsi = 35.0
    atr_pct = 1.2


def _patch_uc(monkeypatch, candles):
    class _FakeUC:
        def __init__(self, exchange):
            pass
        async def execute(self, symbol, timeframe, limit):
            return list(candles)

    monkeypatch.setattr(gc_mod, "GetCandlesUseCase", _FakeUC)


def _patch_entry(monkeypatch):
    monkeypatch.setattr(bot_mod, "evaluate_entry", lambda c, cfg: _Sig())


def _candles(n=70):
    from decimal import Decimal
    from app.domain.entities.candle import Candle
    return [
        Candle(
            time=1000 + i,
            open=Decimal("100"),
            high=Decimal("101"),
            low=Decimal("99"),
            close=Decimal("100"),
            volume=Decimal("10"),
        )
        for i in range(n)
    ]


class TestPaperWiring:
    @pytest.mark.asyncio
    async def test_check_symbols_creates_paper_position_in_paper_mode(self, monkeypatch):
        """paper_mode=True + signal → both _log_signal AND _paper_entry run."""
        _patch_uc(monkeypatch, _candles())
        _patch_entry(monkeypatch)

        bot = ScalpMasterBot()
        bot.config.symbols = ["TESTSYM"]
        assert bot.state.paper_mode is True

        await bot._check_symbols(object())

        assert len(bot.state.recent_signals) == 1
        assert len(bot.state.open_positions) == 1, "P2c: paper position must be created"
        pos = bot.state.open_positions[0]
        assert pos.symbol == "TESTSYM"
        assert pos.bot_slug == "scalp_master"
        assert pos.quantity == 900.0

    @pytest.mark.asyncio
    async def test_check_symbols_skips_paper_position_outside_paper_mode(self, monkeypatch):
        """paper_mode=False + signal → only _log_signal (no virtual position)."""
        _patch_uc(monkeypatch, _candles())
        _patch_entry(monkeypatch)

        bot = ScalpMasterBot()
        bot.config.symbols = ["TESTSYM"]
        bot.state.paper_mode = False

        await bot._check_symbols(object())

        assert len(bot.state.recent_signals) == 1
        assert bot.state.open_positions == []
