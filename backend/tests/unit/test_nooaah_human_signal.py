"""RED tests for HumanSignal in Nooaah (ADR-0037).

EXPECTED TO FAIL until implementation adds:
  - NooaahState.human_direction: str = "neutral"
  - NooaahState.human_expires_at: int = 0
  - NooaahState.human_blocks_entry property

Mode 1 (safety filter): HumanSignal only vetoes bearish. ML stays in charge.
"""
from __future__ import annotations

import time

from app.services.bots.nooaah.state import NooaahState


class TestHumanBlocksEntry:
    """State-level: human_blocks_entry helper (mode 1 — safety filter)."""

    def test_default_state_no_block(self) -> None:
        """New state: neutral, no expiry → does not block."""
        s = NooaahState()
        assert s.human_direction == "neutral"
        assert s.human_expires_at == 0
        assert s.human_blocks_entry is False

    def test_human_bearish_blocks_entry(self) -> None:
        """bearish + no expiry → blocks."""
        s = NooaahState()
        s.human_direction = "bearish"
        s.human_expires_at = 0
        assert s.human_blocks_entry is True

    def test_human_neutral_does_not_block(self) -> None:
        """neutral → does not block (ML decides)."""
        s = NooaahState()
        s.human_direction = "neutral"
        s.human_expires_at = 0
        assert s.human_blocks_entry is False

    def test_human_bullish_does_not_block(self) -> None:
        """bullish → does NOT force entry (mode 1). Just doesn\'t block."""
        s = NooaahState()
        s.human_direction = "bullish"
        s.human_expires_at = 0
        assert s.human_blocks_entry is False

    def test_human_expired_signal_ignored(self) -> None:
        """bearish but expired → does not block."""
        s = NooaahState()
        s.human_direction = "bearish"
        s.human_expires_at = int(time.time()) - 3600  # expired 1h ago
        assert s.human_blocks_entry is False


class TestHumanSignalVetoIntegration:
    """Integration: bearish vetoes ML entry in run_cycle (ADR-0037 test 6)."""

    async def test_human_bearish_vetoes_ml_entry(self, tmp_path) -> None:
        """run_cycle with bearish + entries_allowed=True -> action=blocked_by_human."""
        from unittest.mock import AsyncMock, MagicMock
        from app.services.bots.nooaah.runner import NooaahRunner
        from app.services.bots.nooaah.state import NooaahState
        from app.services.bots.nooaah.strategy import TradeProposal

        # Setup state file with bearish signal + capital
        state_file = tmp_path / "state.json"
        s = NooaahState(
            capital_total=1000.0,
            capital_available=1000.0,
            human_direction="bearish",
            human_expires_at=0,
        )
        s.save(state_file)

        exchange = MagicMock()
        runner = NooaahRunner(exchange=exchange, state_path=state_file)

        # Mock bot.run_once to return a proposal (if veto fails, position would open)
        mock_result = MagicMock()
        mock_result.proposal = TradeProposal(
            "BTCTMN", "BUY", 100.0, 105.0, 98.0, 90, "trending_up", ""
        )
        mock_result.symbols_analyzed = ["BTCTMN"]
        runner._bot.run_once = AsyncMock(return_value=mock_result)

        await runner.run_cycle(entries_allowed=True)

        # Veto should have fired
        assert runner.state.cycle_logs[-1].action == "blocked_by_human"
        # ML should NOT have been consulted (veto fires before _try_open_new)
        runner._bot.run_once.assert_not_called()
        # No position opened
        assert len(runner.state.open_positions) == 0
