"""Phase 2E: all-bots backtest — standardize + dispatch."""
from app.domain.entities.candle import Candle
from decimal import Decimal


class TestStandardize:

    def test_normalize_bear(self):
        from scripts.all_bots_backtest import standardize_bear
        r = {"total_trades": 5, "wins": 3, "total_pnl_pct": 8.5, "total_fees": 200}
        s = standardize_bear("Q2-2022", r)
        assert s["bot"] == "bear_hunter"
        assert s["trades"] == 5
        assert s["win_rate"] == 60.0

    def test_normalize_nooaah(self):
        from scripts.all_bots_backtest import standardize_nooaah
        from app.services.backtest import BacktestResult
        r = BacktestResult(symbol="X", timeframe="1h", candles_analyzed=100,
                           total_trades=8, win_rate=50.0, total_return_pct=3.0,
                           profit_factor=1.4, max_drawdown_pct=5.0)
        s = standardize_nooaah("Q4-2023", r)
        assert s["bot"] == "nooaah"
        assert s["pf"] == 1.4
        assert s["pnl_pct"] == 3.0
