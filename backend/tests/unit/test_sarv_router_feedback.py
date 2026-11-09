"""Phase 4 MVP: FeedbackTrail tests (ADR-0043)."""
import json
import pytest
from pathlib import Path
from app.services.bots.sarv_router.feedback import FeedbackEntry, FeedbackTrail


class TestFeedbackTrail:
    def test_entry_to_dict(self):
        entry = FeedbackEntry(tick_id="abc", action="switched", user_choice="accept", timestamp="2026-11-09T12:00:00Z")
        d = entry.to_dict()
        assert d["tick_id"] == "abc"
        assert d["user_choice"] == "accept"

    def test_write_and_read(self, tmp_path):
        trail = FeedbackTrail(base_dir=tmp_path)
        entry = FeedbackEntry(tick_id="abc", action="switched", user_choice="accept", timestamp="2026-11-09T12:00:00Z")
        trail.write("u1", entry)
        path = tmp_path / "u1.feedback.jsonl"
        assert path.exists()
        with open(path) as f:
            lines = f.readlines()
        assert len(lines) == 1
        data = json.loads(lines[0])
        assert data["tick_id"] == "abc"

    def test_append_only(self, tmp_path):
        trail = FeedbackTrail(base_dir=tmp_path)
        trail.write("u1", FeedbackEntry(tick_id="abc", action="switched", user_choice="accept", timestamp="t1"))
        trail.write("u1", FeedbackEntry(tick_id="xyz", action="pending", user_choice="reject", timestamp="t2"))
        with open(tmp_path / "u1.feedback.jsonl") as f:
            lines = f.readlines()
        assert len(lines) == 2

    def test_fail_safe_on_read_corrupt(self, tmp_path):
        trail = FeedbackTrail(base_dir=tmp_path)
        path = tmp_path / "u1.feedback.jsonl"
        path.write_text("NOT JSON\n")
        # read_all should not raise
        entries = trail.read_all("u1")
        assert len(entries) == 0
