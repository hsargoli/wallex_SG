"""P1: paper_mode must exist on ScalpState, default True (fail-safe)."""


class TestPaperModeField:
    """P1 — paper_mode field on ScalpState (fail-safe: paper-first)."""

    def test_paper_mode_enabled_by_default(self):
        """ScalpState must have paper_mode=True by default."""
        from app.services.bots.scalp_master.bot import ScalpState
        state = ScalpState()
        assert hasattr(state, "paper_mode"), "ScalpState must have paper_mode field (P1)"
        assert state.paper_mode is True, "paper_mode must default to True (fail-safe)"
