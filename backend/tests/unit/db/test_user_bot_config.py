"""Phase A: UserBotConfig model contract."""
import uuid
from decimal import Decimal
import pytest
from sqlalchemy import inspect


class TestUserBotConfig:
    def test_model_exists_and_instantiates(self):
        from app.infrastructure.db.models.user_bot_config import UserBotConfig
        cfg = UserBotConfig(
            user_id=uuid.uuid4(),
            bot_slug="scalp_master",
            mode="paper",
            capital_allocated=Decimal("100000.00"),
        )
        assert cfg.mode == "paper"
        assert cfg.bot_slug == "scalp_master"

    def test_defaults_for_safety_layers(self):
        """Check that server_default is declared on the columns (no DB needed)."""
        from app.infrastructure.db.models.user_bot_config import UserBotConfig
        for col_name in ("mode", "is_active", "live_stage", "daily_loss_limit_pct", "kill_switch_auto", "kill_switch_manual"):
            col = UserBotConfig.__table__.columns[col_name]
            assert col.server_default is not None, f"{col_name} must have server_default"

    def test_unique_constraint_declared(self):
        from app.infrastructure.db.models.user_bot_config import UserBotConfig
        insp = inspect(UserBotConfig)
        constraints = [c.name for c in insp.local_table.constraints]
        assert "uix_user_bot" in constraints
