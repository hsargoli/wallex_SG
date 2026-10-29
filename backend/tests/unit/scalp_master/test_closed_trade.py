"""Phase 1A-1: ClosedTrade + ScalpState.closed_trades."""
import pytest


class TestClosedTrade:
    def test_closed_trade_dataclass_exists(self):
        from app.services.bots.scalp_master.state import ClosedTrade
        ct = ClosedTrade(
            symbol="BTCTMN", side="BUY",
            entry_price=100.0, exit_price=105.0, quantity=900.0,
            tp=110.0, sl=95.0,
            entry_time=1000, exit_time=2000,
            pnl_net=4500.0, exit_reason="take_profit",
            bot_slug="scalp_master",
        )
        assert ct.exit_reason == "take_profit"
        assert ct.pnl_net == 4500.0

    def test_scalp_state_has_closed_trades(self):
        from app.services.bots.scalp_master.state import ScalpState
        s = ScalpState()
        assert hasattr(s, "closed_trades")
        assert s.closed_trades == []
