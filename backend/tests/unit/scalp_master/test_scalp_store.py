"""Phase B1: ScalpStore must save/load ScalpState per user_id."""
import uuid
from pathlib import Path
import pytest
from app.services.bots.scalp_master.bot import ScalpState


class TestScalpStore:
    def test_save_and_load_state(self, tmp_path):
        from app.services.bots.scalp_master.store import ScalpStore
        
        # Use tmp_path to avoid polluting real data dir
        store = ScalpStore(base_dir=tmp_path)
        user_id = str(uuid.uuid4())
        
        state = ScalpState(capital=500000.0, paper_mode=False)
        state.check_count = 42
        
        store.save(user_id, state)
        
        # Verify file exists
        expected_path = tmp_path / f"{user_id}.json"
        assert expected_path.exists(), "state file must be created"
        
        # Load and verify
        loaded = store.load(user_id)
        assert loaded.capital == 500000.0
        assert loaded.paper_mode is False
        assert loaded.check_count == 42

    def test_load_returns_default_if_missing(self, tmp_path):
        from app.services.bots.scalp_master.store import ScalpStore
        store = ScalpStore(base_dir=tmp_path)
        user_id = str(uuid.uuid4())
        
        loaded = store.load(user_id)
        assert loaded.capital == 300_000.0  # default
        assert loaded.paper_mode is True    # default
        assert loaded.check_count == 0
