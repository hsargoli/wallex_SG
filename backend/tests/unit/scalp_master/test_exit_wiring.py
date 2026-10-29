"""Phase 1A-3: _check_symbols must auto-close positions via evaluate_exit."""
import time
from decimal import Decimal

import pytest
from app.domain.entities.candle import Candle
from app.domain.entities.paper_position import PaperPosition
from app.services.bots.scalp_master.bot import ScalpMasterBot


def _candles(high="108", low="102", close="105", n=70):
    return [
        Candle(
            time=1000 + i,
            open=Decimal("105"), high=Decimal(high), low=Decimal(low),
            close=Decimal(close), volume=Decimal("10"),
        )
        for i in range(n)
    ]


def _seed(bot, user_id, entry_time, entry=100.0, tp=110.0, sl=95.0):
    pos = PaperPosition(
        symbol="BTCTMN", side="BUY",
        entry_price=entry, quantity=900.0,
        tp=tp, sl=sl,
        entry_time=entry_time, entry_idx=0,
        reason="seed", bot_slug="scalp_master",
    )
    bot._get_state(user_id).open_positions.append(pos)


def _patch_uc(monkeypatch, candles_fn):
    import app.application.use_cases.get_candles as gc_mod
    class _UC:
        def __init__(self, exchange): pass
        async def execute(self, symbol, timeframe, limit):
            return candles_fn()
    monkeypatch.setattr(gc_mod, "GetCandlesUseCase", _UC)


class TestExitWiring:
    @pytest.mark.asyncio
    async def test_tp_hit_closes_position(self, monkeypatch, tmp_path):
        from app.services.bots.scalp_master.store import ScalpStore
        bot = ScalpMasterBot()
        bot.store = ScalpStore(base_dir=tmp_path); bot._states = {}
        bot.config.symbols = ["BTCTMN"]
        _seed(bot, "u1", entry_time=int(time.time()) - 3600)  # 1h ago, not timeout
        _patch_uc(monkeypatch, lambda: _candles(high="111", low="104", close="108"))

        await bot._check_symbols(object(), user_id="u1")

        s = bot._get_state("u1")
        assert s.open_positions == []
        assert len(s.closed_trades) == 1
        assert s.closed_trades[0].exit_reason == "take_profit"
        assert s.closed_trades[0].exit_price == 110.0

    @pytest.mark.asyncio
    async def test_sl_hit_closes_position(self, monkeypatch, tmp_path):
        from app.services.bots.scalp_master.store import ScalpStore
        bot = ScalpMasterBot()
        bot.store = ScalpStore(base_dir=tmp_path); bot._states = {}
        bot.config.symbols = ["BTCTMN"]
        _seed(bot, "u1", entry_time=int(time.time()) - 3600)
        _patch_uc(monkeypatch, lambda: _candles(high="104", low="94", close="95"))

        await bot._check_symbols(object(), user_id="u1")

        s = bot._get_state("u1")
        assert s.open_positions == []
        assert s.closed_trades[0].exit_reason == "stop_loss"
        assert s.closed_trades[0].exit_price == 95.0

    @pytest.mark.asyncio
    async def test_timeout_closes_position(self, monkeypatch, tmp_path):
        from app.services.bots.scalp_master.store import ScalpStore
        bot = ScalpMasterBot()
        bot.store = ScalpStore(base_dir=tmp_path); bot._states = {}
        bot.config.symbols = ["BTCTMN"]
        # 25h ago > timeout 24 candles * 1h
        _seed(bot, "u1", entry_time=int(time.time()) - 25 * 3600)
        _patch_uc(monkeypatch, lambda: _candles(high="108", low="102", close="105"))

        await bot._check_symbols(object(), user_id="u1")

        s = bot._get_state("u1")
        assert s.open_positions == []
        assert s.closed_trades[0].exit_reason == "timeout"

    @pytest.mark.asyncio
    async def test_no_exit_keeps_position_open(self, monkeypatch, tmp_path):
        from app.services.bots.scalp_master.store import ScalpStore
        bot = ScalpMasterBot()
        bot.store = ScalpStore(base_dir=tmp_path); bot._states = {}
        bot.config.symbols = ["BTCTMN"]
        _seed(bot, "u1", entry_time=int(time.time()) - 3600)
        _patch_uc(monkeypatch, lambda: _candles(high="105", low="100", close="103"))

        await bot._check_symbols(object(), user_id="u1")

        s = bot._get_state("u1")
        assert len(s.open_positions) == 1
        assert s.closed_trades == []
