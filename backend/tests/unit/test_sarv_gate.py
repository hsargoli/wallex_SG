"""Phase 2A: Gate — shared flag for nooaah entry control (zero coupling)."""
import json


class TestGate:
    def test_default_true_when_file_missing(self, tmp_path):
        from app.services.bots.sarv_router.gate import read_gate
        g = read_gate(path=tmp_path / "missing.json")
        assert g.allow_new_entries is True
        assert g.regime == "unknown"

    def test_write_then_read(self, tmp_path):
        from app.services.bots.sarv_router.gate import read_gate, write_gate
        p = tmp_path / "gate.json"
        write_gate(False, "downtrend", path=p)
        g = read_gate(path=p)
        assert g.allow_new_entries is False
        assert g.regime == "downtrend"

    def test_corrupted_file_returns_true(self, tmp_path):
        from app.services.bots.sarv_router.gate import read_gate
        p = tmp_path / "gate.json"
        p.write_text("not valid json{")
        g = read_gate(path=p)
        assert g.allow_new_entries is True

    def test_write_creates_parent_dir(self, tmp_path):
        from app.services.bots.sarv_router.gate import write_gate
        p = tmp_path / "nested" / "subdir" / "gate.json"
        write_gate(True, "uptrend", path=p)
        assert p.exists()
        assert p.parent.is_dir()

    def test_updated_at_timestamp(self, tmp_path):
        from app.services.bots.sarv_router.gate import read_gate, write_gate
        p = tmp_path / "gate.json"
        write_gate(True, "uptrend", path=p)
        g = read_gate(path=p)
        assert "T" in g.updated_at
