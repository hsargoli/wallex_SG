"""P2a: ScalpState.open_positions (list of PaperPosition)."""


class TestPaperStateField:
    """P2a — open_positions field on ScalpState."""

    def test_scalp_state_has_open_positions(self):
        """ScalpState must expose open_positions (default: empty list)."""
        from app.services.bots.scalp_master.bot import ScalpState
        from app.domain.entities.paper_position import PaperPosition

        state = ScalpState()
        assert hasattr(state, "open_positions"), "ScalpState must have open_positions (P2a)"
        assert state.open_positions == [], "default must be empty list"

        # sanity — accept a PaperPosition (domain entity, bot_slug aware)
        state.open_positions.append(
            PaperPosition(
                symbol="BTCTMN",
                side="BUY",
                entry_price=100.0,
                quantity=1.0,
                tp=110.0,
                sl=95.0,
                entry_time=0,
                entry_idx=0,
                reason="test",
                bot_slug="scalp_master",
            )
        )
        assert len(state.open_positions) == 1
        assert state.open_positions[0].bot_slug == "scalp_master"
