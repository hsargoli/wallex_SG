"""Phase 1A-2: _paper_exit (close position, compute net PnL with fees)."""
import pytest
from app.domain.entities.paper_position import PaperPosition
from app.services.bots.scalp_master.state import ScalpState
from app.services.bots.scalp_master.bot import ScalpMasterBot


def _seed_position(bot, user_id="u1", entry=100.0, qty=900.0):
    pos = PaperPosition(
        symbol="BTCTMN", side="BUY",
        entry_price=entry, quantity=qty,
        tp=110.0, sl=95.0,
        entry_time=1000, entry_idx=0,
        reason="seed", bot_slug="scalp_master",
    )
    s = bot._get_state(user_id)
    s.open_positions.append(pos)
    return pos


class TestPaperExit:
    def test_exit_on_take_profit_updates_capital(self, tmp_path):
        from app.services.bots.scalp_master.store import ScalpStore
        bot = ScalpMasterBot()
        bot.store = ScalpStore(base_dir=tmp_path)
        bot._states = {}
        _seed_position(bot, entry=100.0, qty=900.0)
        capital_before = bot._get_state("u1").capital

        result = bot._paper_exit("BTCTMN", 110.0, "take_profit", user_id="u1")

        assert result is not None
        # gross = (110-100)*900 = 9000
        # fee = fee_pct(0.2%) * amount_in * 2 sides ≈ 0.004 * 100000 = 200*0.9 = 180*... hmm
        # We use: fee = fee_pct/100 * (entry*quantity) * 2 = 0.002 * 90000 * 2 = 360
        # net = 9000 - 360 = 8640
        assert result.exit_reason == "take_profit"
        assert result.exit_price == 110.0
        assert 8000.0 < result.pnl_net < 9500.0  # tolerate fee rounding
        s = bot._get_state("u1")
        assert s.open_positions == []
        assert len(s.closed_trades) == 1
        assert s.capital > capital_before

    def test_exit_on_stop_loss_reduces_capital(self, tmp_path):
        from app.services.bots.scalp_master.store import ScalpStore
        bot = ScalpMasterBot()
        bot.store = ScalpStore(base_dir=tmp_path)
        bot._states = {}
        _seed_position(bot, entry=100.0, qty=900.0)
        capital_before = bot._get_state("u1").capital

        result = bot._paper_exit("BTCTMN", 95.0, "stop_loss", user_id="u1")

        assert result is not None
        assert result.pnl_net < 0
        assert bot._get_state("u1").capital < capital_before

    def test_exit_no_position_returns_none(self, tmp_path):
        from app.services.bots.scalp_master.store import ScalpStore
        bot = ScalpMasterBot()
        bot.store = ScalpStore(base_dir=tmp_path)
        bot._states = {}
        result = bot._paper_exit("NOTEXIST", 100.0, "timeout", user_id="u1")
        assert result is None
