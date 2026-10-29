"""Phase B2: ScalpMasterBot must isolate state per user_id."""
import pytest
from app.services.bots.scalp_master.bot import ScalpMasterBot
from app.services.bots.scalp_master.state import ScalpState
from app.services.bots.scalp_master.store import ScalpStore


class _Sig:
    should_trade = True
    action = "buy"
    entry_price = 100.0
    take_profit = 110.0
    stop_loss = 95.0
    reason = "test-signal"
    drop_pct = 3.0
    rsi = 35.0
    atr_pct = 1.2


class TestScalpPerUser:
    def test_state_is_isolated_per_user(self, tmp_path):
        bot = ScalpMasterBot()
        bot.store = ScalpStore(base_dir=tmp_path)

        user_a = "user-a"
        user_b = "user-b"

        pos = bot._paper_entry("BTCTMN", _Sig(), user_id=user_a)
        assert pos is not None

        state_a = bot._get_state(user_a)
        state_b = bot._get_state(user_b)

        assert len(state_a.open_positions) == 1
        assert len(state_b.open_positions) == 0

        # Persistence file per-user
        assert (tmp_path / f"{user_a}.json").exists()
        assert not (tmp_path / f"{user_b}.json").exists()
