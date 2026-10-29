"""Phase 2C-3: ScalpMasterBot must use watchlist when enabled."""
from decimal import Decimal
from unittest.mock import patch

import pytest
from app.domain.entities.candle import Candle


def _c(t, o, h, l, c, v="100"):
    return Candle(time=t, open=Decimal(str(o)), high=Decimal(str(h)),
                  low=Decimal(str(l)), close=Decimal(str(c)),
                  volume=Decimal(str(v)))


class TestBotWatchlist:
    def test_scalp_state_has_watchlist(self):
        from app.services.bots.scalp_master.state import ScalpState
        s = ScalpState()
        assert hasattr(s, "watchlist")
        assert s.watchlist == {}

    @pytest.mark.asyncio
    async def test_check_symbols_uses_watchlist(self, monkeypatch, tmp_path):
        """When watchlist_enabled, dip should go to watchlist (no entry)."""
        from app.services.bots.scalp_master.store import ScalpStore
        from app.services.bots.scalp_master.bot import ScalpMasterBot
        import app.application.use_cases.get_candles as gc_mod

        bot = ScalpMasterBot()
        bot.store = ScalpStore(base_dir=tmp_path)
        bot._states = {}
        bot.config.symbols = ["BTCTMN"]
        bot.config.watchlist_enabled = True

        # 99 flat + 1 crash
        top = 200.0
        end = top * 0.97
        candles = [_c(i * 3600, top, top + 0.5, top - 0.5, top) for i in range(99)]
        candles.append(_c(99 * 3600, top, top + 0.5, end - 1, end))

        class _UC:
            def __init__(self, exchange): pass
            async def execute(self, symbol, timeframe, limit):
                return candles

        monkeypatch.setattr(gc_mod, "GetCandlesUseCase", _UC)

        await bot._check_symbols(object(), user_id="u1")

        state = bot._get_state("u1")
        assert "BTCTMN" in state.watchlist, "dip should enter watchlist"
        assert state.open_positions == [], "should NOT open position yet"
