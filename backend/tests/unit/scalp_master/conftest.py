"""Isolate ScalpStore per test — no pollution of real data dir."""
import pytest
from app.services.bots.scalp_master.store import ScalpStore


@pytest.fixture(autouse=True)
def isolated_store(tmp_path, monkeypatch):
    import app.services.bots.scalp_master.bot as bot_mod
    orig_init = bot_mod.ScalpMasterBot.__init__

    def patched_init(self, config=None):
        orig_init(self, config)
        self.store = ScalpStore(base_dir=tmp_path)
        self._states = {}

    monkeypatch.setattr(bot_mod.ScalpMasterBot, "__init__", patched_init)
    yield
