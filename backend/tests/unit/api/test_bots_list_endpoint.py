"""P7: /v1/bots/list must return dynamic registry (not hardcoded nooaah-only)."""
from fastapi.testclient import TestClient
from app.main import app


class TestBotsListEndpoint:
    """P7+2026-10-30 — /v1/bots/list must include ALL 11 bots.

    Per Hosein 2026-10-30: archived bots appear with `archived: true`
    (transparency). Only `archived: false` bots are actively tradeable.
    """

    def test_list_includes_archived_scalp_master(self):
        """2026-10-30: scalp_master appears with archived=true (transparency)."""
        client = TestClient(app)
        r = client.get("/v1/bots/list")
        assert r.status_code == 200
        data = r.json()
        items_by_slug = {item["slug"]: item for item in data["items"]}
        assert "scalp_master" in items_by_slug, f"scalp_master must appear (archived): {list(items_by_slug)}"
        assert items_by_slug["scalp_master"]["archived"] is True
        assert "nooaah" in items_by_slug, "nooaah must remain in list"
        assert items_by_slug["nooaah"]["archived"] is False

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
