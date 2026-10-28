"""P5+P6: info tier/capabilities + get_status exposure (paper_mode, capital, open_positions)."""
from decimal import Decimal
from app.domain.entities.paper_position import PaperPosition
from app.services.bots.scalp_master.bot import ScalpMasterBot


class TestInfoExposure:
    """P5 — bot must be discoverable as production + paper-capable."""

    def test_info_tier_is_production(self):
        info = ScalpMasterBot().info
        assert info.tier == "production", "scalp_master must be tier=production (P5)"

    def test_info_capabilities_include_paper(self):
        info = ScalpMasterBot().info
        assert "paper" in info.capabilities, "capabilities must include 'paper' (P5)"


class TestStatusExposure:
    """P6 — get_status must expose paper_mode, capital, open_positions."""

    def test_status_includes_paper_mode_and_capital(self):
        bot = ScalpMasterBot()
        st = bot.get_status()
        assert "paper_mode" in st, "get_status must expose paper_mode (P6)"
        assert st["paper_mode"] is True
        assert "capital" in st, "get_status must expose capital (P6)"
        assert st["capital"] == 300_000.0

    def test_status_includes_open_positions(self):
        bot = ScalpMasterBot()
        # seed one virtual position
        bot.state.open_positions.append(
            PaperPosition(
                symbol="X", side="BUY", entry_price=100.0, quantity=900.0,
                tp=110.0, sl=95.0, entry_time=0, entry_idx=0,
                reason="seed", bot_slug="scalp_master",
            )
        )
        st = bot.get_status()
        assert "open_positions" in st, "get_status must expose open_positions (P6)"
        assert isinstance(st["open_positions"], list)
        assert len(st["open_positions"]) == 1
        assert st["open_positions"][0]["symbol"] == "X"
        assert st["open_positions"][0]["quantity"] == 900.0
