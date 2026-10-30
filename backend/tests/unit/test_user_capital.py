"""User capital decisions (RED, per Hosein 2026-10-30).

Registered user = 10,000,000 TMN (was 300k in bots.py, 3M in user.py).
"""
import inspect
from decimal import Decimal

import pytest

from app.presentation.api.v1 import bots as bots_mod
from app.presentation.api.v1 import user as user_mod


class TestUserBotConfigCapital:
    def test_ensure_user_config_creates_10m(self):
        """Source code must contain Decimal(\"10000000\") — not 300000."""
        src = inspect.getsource(bots_mod._ensure_user_config)
        assert "10000000" in src, f"expected 10M in source, got: {src[:500]}"
        assert "300000" not in src, "old 300k still present"

    def test_user_paper_initial_capital_10m(self):
        """user.py StartRequest.initial_capital must default to 10M."""
        classes = [
            c for name, c in inspect.getmembers(user_mod, inspect.isclass)
            if name == "StartRequest"
        ]
        assert classes, "StartRequest not found in user.py"
        sig = inspect.signature(classes[0])
        cap = sig.parameters.get("initial_capital")
        assert cap is not None
        assert cap.default == 10_000_000.0, f"expected 10M, got {cap.default}"
