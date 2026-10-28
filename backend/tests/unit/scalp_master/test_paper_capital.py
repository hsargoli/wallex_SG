"""P2b-pre: ScalpState.capital (TMN) — used for paper position sizing."""


class TestPaperCapitalField:
    """P2b-pre — capital field on ScalpState (TMN)."""

    def test_scalp_state_has_capital(self):
        """ScalpState must expose capital (default 300_000.0 TMN)."""
        from app.services.bots.scalp_master.bot import ScalpState

        state = ScalpState()
        assert hasattr(state, "capital"), "ScalpState must have capital (P2b-pre)"
        assert state.capital == 300_000.0
        assert isinstance(state.capital, float)
