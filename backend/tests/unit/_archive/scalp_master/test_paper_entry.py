"""P2b: _paper_entry — paper-mode position with correct TMN sizing."""


class _Sig:
    should_trade = True
    action = "buy"
    entry_price = 100.0
    take_profit = 110.0
    stop_loss = 95.0
    reason = "test-signal"
    drop_pct = 3.0
    rsi = 35.0
    atr_pct = 1.2


class TestPaperEntry:
    def test_paper_entry_creates_position_in_paper_mode(self):
        from app.services.bots.scalp_master.bot import ScalpMasterBot
        bot = ScalpMasterBot()
        assert bot.state.paper_mode is True
        assert bot.state.capital == 300_000.0
        assert bot.config.position_size_pct == 30.0
        pos = bot._paper_entry("BTCTMN", _Sig())
        assert pos is not None
        assert pos.symbol == "BTCTMN"
        assert pos.side == "BUY"
        assert pos.entry_price == 100.0
        assert pos.quantity == 900.0  # 300k * 30% / 100
        assert pos.tp == 110.0
        assert pos.sl == 95.0
        assert pos.reason == "test-signal"
        assert pos.bot_slug == "scalp_master"
        assert pos.entry_time > 0
        assert len(bot.state.open_positions) == 1

    def test_paper_entry_returns_none_outside_paper_mode(self):
        from app.services.bots.scalp_master.bot import ScalpMasterBot
        bot = ScalpMasterBot()
        bot.state.paper_mode = False
        assert bot._paper_entry("BTCTMN", _Sig()) is None
        assert bot.state.open_positions == []

    def test_paper_entry_rejects_non_positive_price(self):
        from app.services.bots.scalp_master.bot import ScalpMasterBot
        class _Bad:
            should_trade=True; action="buy"; entry_price=0.0
            take_profit=10.0; stop_loss=5.0; reason="bad"
            drop_pct=0.0; rsi=0.0; atr_pct=0.0
        bot = ScalpMasterBot()
        assert bot._paper_entry("X", _Bad()) is None
        assert bot.state.open_positions == []
