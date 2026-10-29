"""SarvTiger: aggressive BTC futures config — 4 safety rules baked in."""


class TestSarvTigerConfig:
    def test_leverage_capped_at_4x(self):
        from app.services.bots.sarv_tiger.config import SarvTigerConfig
        c = SarvTigerConfig()
        assert c.leverage == 4
        assert c.max_leverage == 4
        assert c.leverage <= c.max_leverage

    def test_position_size_20pct(self):
        from app.services.bots.sarv_tiger.config import SarvTigerConfig
        c = SarvTigerConfig()
        assert c.position_size_pct == 20.0
        assert 0 < c.position_size_pct <= 20.0, "position must be 0-20% (risk control)"

    def test_sl_tp_rr_4_to_1(self):
        from app.services.bots.sarv_tiger.config import SarvTigerConfig
        c = SarvTigerConfig()
        assert c.sl_atr_mult == 1.2
        assert c.tp_atr_mult == 8.0
        rr = c.tp_atr_mult / c.sl_atr_mult
        assert abs(rr - 6.67) < 0.02, f"R/R must be 4:1, got {rr:.2f}"

    def test_daily_loss_limit_7pct(self):
        from app.services.bots.sarv_tiger.config import SarvTigerConfig
        c = SarvTigerConfig()
        assert c.daily_loss_limit_pct == 7.0
        assert 0 < c.daily_loss_limit_pct <= 10.0, "must be bounded"

    def test_max_drawdown_25pct(self):
        from app.services.bots.sarv_tiger.config import SarvTigerConfig
        c = SarvTigerConfig()
        assert c.max_drawdown_pct == 25.0

    def test_btc_only_and_4h(self):
        from app.services.bots.sarv_tiger.config import SarvTigerConfig
        c = SarvTigerConfig()
        assert c.symbol == "BTCTMN"
        assert c.timeframe == "4h"
        assert c.max_positions == 1

    def test_bollinger_defaults(self):
        from app.services.bots.sarv_tiger.config import SarvTigerConfig
        c = SarvTigerConfig()
        assert c.bb_period == 20
        assert c.bb_std == 2.0
        assert c.bb_squeeze_threshold == 0.5

    def test_pyramiding(self):
        from app.services.bots.sarv_tiger.config import SarvTigerConfig
        c = SarvTigerConfig()
        assert c.pyramiding_enabled is True
        assert c.pyramiding_add_pct == 30.0
        assert c.pyramiding_step_atr == 1.5
