"""Phase 1A: SarvRouterConfig defaults."""
from app.services.bots.sarv_router.config import SarvRouterConfig


class TestSarvRouterConfig:
    def test_defaults(self):
        c = SarvRouterConfig()
        # Regime detection
        assert c.adx_period == 14
        assert c.ema_period == 50
        assert c.uptrend_adx_min == 25.0
        assert c.downtrend_adx_min == 25.0
        assert c.range_adx_max == 20.0
        assert c.stability_window == 24
        assert c.cooldown_candles == 12
        # Capital allocation
        assert c.uptrend_capital_pct == 60.0
        assert c.range_capital_pct == 30.0
        assert c.downtrend_capital_pct == 0.0
        assert c.cash_reserve_pct == 10.0
        # Risk
        assert c.daily_loss_limit_pct == 2.0
        assert c.max_per_bot_pct == 60.0

    def test_capital_sums_to_100(self):
        c = SarvRouterConfig()
        total = (c.uptrend_capital_pct + c.range_capital_pct
                 + c.downtrend_capital_pct + c.cash_reserve_pct)
        assert total == 100.0, f"capital allocation must sum to 100, got {total}"

    def test_bot_mapping(self):
        c = SarvRouterConfig()
        assert c.uptrend_bot == "nooaah"
        assert c.range_bot == "sarvban"
        assert c.downtrend_bot is None  # cash, no bot
