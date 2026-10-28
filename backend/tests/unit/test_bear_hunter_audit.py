"""Test: audit.py must use paths.py (absolute), not hardcoded relative."""
from pathlib import Path
import pytest

class TestBearHunterAuditPath:
    def test_audit_path_is_absolute(self):
        """Audit path must be absolute, not relative to CWD."""
        # Import should not fail
        from app.services.bots.bear_hunter.audit import AuditTrail
        # The trail instance should have an absolute path
        from app.services.bots.bear_hunter.audit import audit_trail
        path = Path(audit_trail.path)
        assert path.is_absolute(), f"Expected absolute path, got: {path}"

    def test_audit_path_matches_paths_module(self):
        """Audit path must be under paths.DATA_DIR (consistency)."""
        from app.services.bots.bear_hunter.audit import audit_trail
        from app.services.bots.bear_hunter.paths import DATA_DIR
        audit_path = Path(audit_trail.path)
        assert str(audit_trail.path).startswith(str(DATA_DIR)), \
            f"audit path {audit_trail.path} should be under {DATA_DIR}"
