"""Guest Mode config decisions (RED first, per Hosein's 2026-10-30 decision).

Decisions:
  1. Guest paper capital = 100_000 TMN (was 500_000)
  2. Guest position_size_pct = 30.0 (was 50.0)
  3. GuestScheduler cleanup: states > 24h deleted
"""
import json
import time
from pathlib import Path

import pytest

from app.presentation.api.v1.guest import DEFAULT_GUEST_CAPITAL


class TestGuestCapital:
    def test_guest_capital_is_100k(self):
        """Per Hosein 2026-10-30: guest = 100k TMN."""
        assert DEFAULT_GUEST_CAPITAL == 100_000.0

    def test_guest_position_size_default(self):
        """Per Hosein: guest position size = 30% (was 50%)."""
        from app.presentation.api.v1.guest import StartRequest
        req = StartRequest()
        assert req.position_size_pct == 30.0


class TestGuestCleanup:
    def test_cleanup_removes_stale_states(self, tmp_path):
        """Cleanup must delete state dirs older than 24h."""
        from app.services.guest import cleanup_stale_guests

        # Create two guest dirs: one stale, one fresh
        stale = tmp_path / "stale_guest"
        fresh = tmp_path / "fresh_guest"
        stale.mkdir()
        fresh.mkdir()
        (stale / "state.json").write_text("{}")
        (fresh / "state.json").write_text("{}")

        # Set stale mtime to 25h ago
        old = time.time() - 25 * 3600
        import os
        os.utime(stale, (old, old))

        removed = cleanup_stale_guests(tmp_path, max_age_hours=24)
        assert removed == 1
        assert not stale.exists()
        assert fresh.exists()

    def test_cleanup_keeps_recent(self, tmp_path):
        from app.services.guest import cleanup_stale_guests
        recent = tmp_path / "recent"
        recent.mkdir()
        removed = cleanup_stale_guests(tmp_path, max_age_hours=24)
        assert removed == 0
        assert recent.exists()

    def test_cleanup_handles_missing_dir(self, tmp_path):
        from app.services.guest import cleanup_stale_guests
        removed = cleanup_stale_guests(tmp_path / "nonexistent", max_age_hours=24)
        assert removed == 0
