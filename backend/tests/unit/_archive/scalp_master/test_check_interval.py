"""P8: check_interval_sec must be 1800 (30 minutes) — not 180 (3 minutes)."""
from app.services.bots.scalp_master.config import ScalpMasterConfig


class TestCheckInterval:
    def test_default_interval_is_30_minutes(self):
        """Default check interval must be 1800 seconds (30 min)."""
        cfg = ScalpMasterConfig()
        assert cfg.check_interval_sec == 1800, \
            f"expected 1800 (30m), got {cfg.check_interval_sec}"
