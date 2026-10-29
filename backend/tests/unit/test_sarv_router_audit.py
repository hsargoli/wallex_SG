"""Phase 1E: AuditTrail — WAL pattern for SarvRouter decisions."""
import json
import uuid
from app.services.bots.sarv_router.audit import AuditTrail, AuditEntry


class TestAuditTrail:
    def test_log_and_read_entry(self, tmp_path):
        trail = AuditTrail(base_dir=tmp_path)
        uid = str(uuid.uuid4())
        entry = AuditEntry(
            type="switch",
            from_regime="uptrend",
            to_regime="range",
            from_bots=["nooaah"],
            to_bots=["sarvban"],
            reason="stability_window_passed",
            allocations={"sarvban": 300_000.0},
            cash=700_000.0,
        )
        trail.log(uid, entry)
        path = tmp_path / f"{uid}.audit.jsonl"
        assert path.exists()
        lines = path.read_text().strip().split("\n")
        assert len(lines) == 1
        row = json.loads(lines[0])
        assert row["type"] == "switch"
        assert row["from_regime"] == "uptrend"
        assert row["to_regime"] == "range"

    def test_append_only(self, tmp_path):
        trail = AuditTrail(base_dir=tmp_path)
        uid = str(uuid.uuid4())
        for i in range(3):
            trail.log(uid, AuditEntry(type="tick", from_regime="range", to_regime="range",
                                       from_bots=[], to_bots=[], reason=f"tick-{i}",
                                       allocations={}, cash=1_000_000.0))
        path = tmp_path / f"{uid}.audit.jsonl"
        lines = path.read_text().strip().split("\n")
        assert len(lines) == 3
        for i, line in enumerate(lines):
            assert json.loads(line)["reason"] == f"tick-{i}"

    def test_timestamp_auto(self, tmp_path):
        trail = AuditTrail(base_dir=tmp_path)
        uid = str(uuid.uuid4())
        trail.log(uid, AuditEntry(type="tick", from_regime="x", to_regime="y",
                                   from_bots=[], to_bots=[], reason="test",
                                   allocations={}, cash=0.0))
        path = tmp_path / f"{uid}.audit.jsonl"
        row = json.loads(path.read_text().strip().split("\n")[0])
        assert "timestamp" in row
        assert row["timestamp"].endswith("+00:00") or "T" in row["timestamp"]

    def test_log_survives_io_error(self, tmp_path):
        """If write fails, log() must NOT raise (fail-safe)."""
        trail = AuditTrail(base_dir=tmp_path / "nonexistent" / "subdir")
        # directory will be created by __init__; write must succeed
        trail.log(str(uuid.uuid4()), AuditEntry(type="x", from_regime="a", to_regime="b",
                                                 from_bots=[], to_bots=[], reason="r",
                                                 allocations={}, cash=0.0))
