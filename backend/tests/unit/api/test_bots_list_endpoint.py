"""P7: /v1/bots/list must return dynamic registry (not hardcoded nooaah-only)."""
from fastapi.testclient import TestClient
from app.main import app


class TestBotsListEndpoint:
    """P7 — /v1/bots/list must include scalp_master (and keep nooaah)."""

    def test_list_excludes_archived_scalp_master(self):
        client = TestClient(app)
        r = client.get("/v1/bots/list")
        assert r.status_code == 200
        data = r.json()
        slugs = [item["slug"] for item in data["items"]]
        assert "scalp_master" not in slugs, f"archived scalp_master must NOT appear: {slugs}"
        assert "nooaah" in slugs, "nooaah must remain in list"

    def test_list_production_tier_present(self):
        client = TestClient(app)
        r = client.get("/v1/bots/list")
        data = r.json()
        nooaah = next((x for x in data["items"] if x["slug"] == "nooaah"), None)
        assert nooaah is not None
        assert nooaah["tier"] == "production"

    def test_list_filters_by_tier(self):
        client = TestClient(app)
        r = client.get("/v1/bots/list?tier=production")
        data = r.json()
        for item in data["items"]:
            assert item["tier"] == "production"
