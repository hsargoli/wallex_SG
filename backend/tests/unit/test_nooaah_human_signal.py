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
