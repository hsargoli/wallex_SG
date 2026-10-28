"""Phase C1: /bots/{slug}/start|stop|status require auth + pass user_id."""
import uuid
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.presentation.api.v1.auth import require_user_token
from app.services.bots import bot_registry


def _fake_user(user_id: str = "user-a") -> dict:
    return {"sub": user_id}


class TestBotsApiAuth:
    def test_start_requires_auth(self):
        with TestClient(app) as client:
            r = client.post("/v1/bots/scalp_master/start")
            assert r.status_code == 401, f"expected 401, got {r.status_code}"

    def test_status_requires_auth(self):
        with TestClient(app) as client:
            r = client.get("/v1/bots/scalp_master/status")
            assert r.status_code == 401

    def test_start_passes_user_id_to_bot(self):
        bot = bot_registry.get("scalp_master")
        assert bot is not None

        fake_exchange = object()
        with patch.object(bot, "start", new=AsyncMock(return_value={"status": "started"})) as mock_start:
            app.dependency_overrides[require_user_token] = lambda: _fake_user("user-a")
            try:
                with TestClient(app) as client:
                    client.app.state.exchange = fake_exchange
                    r = client.post("/v1/bots/scalp_master/start")
                    assert r.status_code == 200, r.text
                    assert mock_start.called
                    _, kwargs = mock_start.call_args
                    assert kwargs.get("user_id") == "user-a", f"user_id not passed: {kwargs}"
            finally:
                app.dependency_overrides.clear()
