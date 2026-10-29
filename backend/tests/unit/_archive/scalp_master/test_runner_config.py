"""Phase 2C-5: runner must pass custom config (watchlist_enabled) to backtest."""
from decimal import Decimal
import pytest
from app.domain.entities.candle import Candle


class TestRunnerConfig:
    def test_run_period_passes_config(self, monkeypatch):
        import scripts.scalp_backtest_runner as r
        from app.services.bots.scalp_master.config import ScalpMasterConfig

        captured = {}

        def fake_backtest(candles, **kwargs):
            captured["config"] = kwargs.get("config")
            return {"total_trades": 0, "win_rate": 0.0, "total_pnl": 0.0,
                    "total_pnl_pct": 0.0, "profit_factor": None, "max_drawdown_pct": 0.0}

        monkeypatch.setattr(
            "app.infrastructure.backtest.bot_backtest.run_scalp_backtest",
            fake_backtest
        )

        cfg = ScalpMasterConfig(watchlist_enabled=True, trend_filter_enabled=True)
        candles = [Candle(time=i*3600, open=Decimal("100"), high=Decimal("101"),
                          low=Decimal("99"), close=Decimal("100"), volume=Decimal("10"))
                   for i in range(100)]

        r.run_period(candles, "test", initial_capital=10_000.0,
                     fee_pct=0.2, slippage_pct=0.1, spread_pct=0.05, config=cfg)
        assert captured["config"] is not None
        assert captured["config"].watchlist_enabled is True
        assert captured["config"].trend_filter_enabled is True
