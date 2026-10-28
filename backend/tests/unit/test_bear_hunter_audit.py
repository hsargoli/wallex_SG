"""Test: audit.py must use paths.py (absolute), not hardcoded relative."""
import json
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


class TestAuditTrailWAL:
    """WAL must actually write to disk — not just resolve a path."""

    @pytest.mark.asyncio
    async def test_log_trade_intent_writes_to_disk(self, tmp_path):
        """Intent must be persisted to disk BEFORE exchange (WAL step 1)."""
        from app.services.bots.bear_hunter.audit import AuditTrail
        p = tmp_path / "audit.jsonl"
        trail = AuditTrail(file_path=p)
        audit_id = await trail.log_trade_intent(signal={"x": 1}, dry_run_result=None)
        assert p.exists(), "intent file must be created"
        lines = [l for l in p.read_text().strip().split("\n") if l]
        assert len(lines) == 1
        entry = json.loads(lines[-1])
        assert entry["type"] == "trade_intent"
        assert entry["audit_id"] == audit_id

    @pytest.mark.asyncio
    async def test_log_trade_success_appends(self, tmp_path):
        """Success must append (not overwrite) — WAL step 2."""
        from app.services.bots.bear_hunter.audit import AuditTrail
        p = tmp_path / "audit.jsonl"
        trail = AuditTrail(file_path=p)
        aid = await trail.log_trade_intent(signal={}, dry_run_result=None)
        class _Pos:
            position_id = "pos-1"
            entry_price = 100
        await trail.log_trade_success(aid, _Pos())
        lines = [l for l in p.read_text().strip().split("\n") if l]
        assert len(lines) == 2, f"expected 2 WAL lines, got {len(lines)}"
        last = json.loads(lines[-1])
        assert last["type"] == "trade_success"
        assert last["audit_id"] == aid
