class TestGetBudget:
    def test_get_initial_budget(self, client):
        r = client.get("/v1/bot/budget")
        assert r.status_code == 200
        data = r.json()
        assert data["allocated_budget"] == "100000"
        assert data["in_use_capital"] == "0"
        assert data["available_for_trade"] == "100000"
        assert data["currency"] == "TMN"


class TestPostBudget:
    def test_update_budget_valid(self, client):
        r = client.post("/v1/bot/budget", json={"allocated_budget": 50000})
        assert r.status_code == 200
        data = r.json()
        assert data["allocated_budget"] == "50000"
        assert data["available_for_trade"] == "50000"

    def test_update_persists_across_requests(self, client):
        client.post("/v1/bot/budget", json={"allocated_budget": 75000})
        r = client.get("/v1/bot/budget")
        assert r.json()["allocated_budget"] == "75000"

    def test_update_with_decimal(self, client):
        r = client.post("/v1/bot/budget", json={"allocated_budget": 123456.78})
        assert r.status_code == 200
        assert r.json()["allocated_budget"] == "123456.78"

    def test_negative_budget_rejected(self, client):
        r = client.post("/v1/bot/budget", json={"allocated_budget": -100})
        assert r.status_code == 422

    def test_zero_budget_rejected(self, client):
        r = client.post("/v1/bot/budget", json={"allocated_budget": 0})
        assert r.status_code == 422

    def test_missing_field_rejected(self, client):
        r = client.post("/v1/bot/budget", json={})
        assert r.status_code == 422

    def test_wrong_type_rejected(self, client):
        r = client.post("/v1/bot/budget", json={"allocated_budget": "not-a-number"})
        assert r.status_code == 422

    def test_update_below_in_use_returns_400(self, client):
        # اول ۵۰ هزار تومان رزرو کن (شبیه‌سازی سفارش باز)
        from app.services.budget_service import budget_service

        budget_service.allocate_for_order(50000)

        # حالا تلاش کن بودجه رو به ۳۰ هزار کاهش بدی
        r = client.post("/v1/bot/budget", json={"allocated_budget": 30000})
        assert r.status_code == 400
        assert "cannot be lower than capital currently in use" in r.json()["detail"]
