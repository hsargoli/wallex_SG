"""Cleanup must use meta.json.last_seen_at, NOT directory mtime.

Bug (2026-10-31): active guests could be deleted because dir mtime
doesn't update when meta.json is overwritten (in-place).
"""
import json
import time
from pathlib import Path

import pytest

from app.services.guest.storage import cleanup_stale_guests


def _mk_guest(base: Path, token: str, last_seen_hours_ago: float) -> Path:
    """Create a guest dir with meta.json having specific last_seen_at."""
    d = base / token
    d.mkdir(parents=True)
    last_seen = int(time.time() - last_seen_hours_ago * 3600)
    meta = {"created_at": last_seen, "last_seen_at": last_seen}
    (d / "meta.json").write_text(json.dumps(meta))
    (d / "state.json").write_text("{}")
    return d


class TestCleanupUsesLastSeenAt:
    def test_recent_last_seen_kept(self, tmp_path):
        """Guest with last_seen_at = 1h ago must be KEPT."""
        d = _mk_guest(tmp_path, "recent", last_seen_hours_ago=1)
        # Force dir mtime to be OLD (simulating in-place overwrite)
        import os
        old = time.time() - 48 * 3600
        os.utime(d, (old, old))

        removed = cleanup_stale_guests(tmp_path, max_age_hours=24)
        assert removed == 0, f"recent guest should NOT be removed"
        assert d.exists(), "recent guest dir must remain"

    def test_stale_last_seen_removed(self, tmp_path):
        """Guest with last_seen_at = 25h ago must be REMOVED."""
        d = _mk_guest(tmp_path, "stale", last_seen_hours_ago=25)
        # Force dir mtime to be NEW (opposite of the bug)
        import os
        new = time.time()
        os.utime(d, (new, new))

        removed = cleanup_stale_guests(tmp_path, max_age_hours=24)
        assert removed == 1, f"stale guest should be removed"
        assert not d.exists()

    def test_missing_meta_falls_back_to_dir_mtime(self, tmp_path):
        """No meta.json → use dir mtime as fallback."""
        d = tmp_path / "no_meta"
        d.mkdir()
        (d / "state.json").write_text("{}")
        import os
        old = time.time() - 48 * 3600
        os.utime(d, (old, old))

        removed = cleanup_stale_guests(tmp_path, max_age_hours=24)
        assert removed == 1

    def test_corrupt_meta_uses_dir_mtime(self, tmp_path):
        """Corrupt meta.json → fallback to dir mtime."""
        d = tmp_path / "corrupt"
        d.mkdir()
        (d / "meta.json").write_text("not json {{{")
        (d / "state.json").write_text("{}")
        import os
        old = time.time() - 48 * 3600
        os.utime(d, (old, old))

        removed = cleanup_stale_guests(tmp_path, max_age_hours=24)
        assert removed == 1
