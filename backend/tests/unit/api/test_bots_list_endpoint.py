"""P7: /v1/bots/list must return dynamic registry (not hardcoded nooaah-only)."""
from fastapi.testclient import TestClient
from app.main import app


class TestBotsListEndpoint:
    """P7 — /v1/bots/list must include scalp_master (and keep nooaah)."""

    def test_list_includes_scalp_master(self):
        client = TestClient(app)
        r = client.get("/v1/bots/list")
        assert r.status_code == 200
        data = r.json()
        assert data["count"] >= 2, "must include at least nooaah + scalp_master"
        slugs = [item["slug"] for item in data["items"]]
        assert "scalp_master" in slugs, f"scalp_master missing. got: {slugs}"
        assert "nooaah" in slugs, "nooaah must remain in list"

    def test_list_includes_paper_capability(self):
        client = TestClient(app)
        r = client.get("/v1/bots/list")
        data = r.json()
        scalp = next((x for x in data["items"] if x["slug"] == "scalp_master"), None)
        assert scalp is not None
        assert scalp["tier"] == "production"

    def test_list_filters_by_tier(self):
        client = TestClient(app)
        r = client.get("/v1/bots/list?tier=production")
        data = r.json()
        for item in data["items"]:
            assert item["tier"] == "production"
