"""Phase 2A-3: backtest runner (CSV loader, date filter, B&H, Cash)."""
from decimal import Decimal


def _csv_content() -> str:
    return (
        "open_time,open,high,low,close,volume\n"
        "1609459200,100,101,99,100,10\n"
        "1609462800,100,101,99,105,10\n"
        "1609466400,105,106,104,104,10\n"
        "1609470000,104,105,103,100,10\n"
    )


class TestBacktestRunner:
    def test_load_candles_csv(self, tmp_path):
        from scripts.scalp_backtest_runner import load_candles_csv
        p = tmp_path / "x.csv"
        p.write_text(_csv_content())
        candles = load_candles_csv(p)
        assert len(candles) == 4
        assert candles[0].close == Decimal("100")
        assert candles[1].close == Decimal("105")
        assert candles[0].time == 1609459200

    def test_filter_by_date(self, tmp_path):
        from scripts.scalp_backtest_runner import load_candles_csv, filter_by_date
        p = tmp_path / "x.csv"
        p.write_text(_csv_content())
        candles = load_candles_csv(p)
        out = filter_by_date(candles, start_ts=1609466400, end_ts=1609470000)
        assert len(out) == 2
        assert out[0].time == 1609466400

    def test_buy_and_hold_pnl(self, tmp_path):
        from scripts.scalp_backtest_runner import load_candles_csv, buy_and_hold
        p = tmp_path / "x.csv"
        p.write_text(_csv_content())
        candles = load_candles_csv(p)
        r0 = buy_and_hold(candles, initial_capital=10_000.0, fee_pct=0.0)
        assert r0["total_pnl"] == 0.0
        assert r0["total_pnl_pct"] == 0.0
        r2 = buy_and_hold(candles, initial_capital=10_000.0, fee_pct=0.2)
        assert r2["total_pnl"] < 0
        assert -50.0 < r2["total_pnl"] < 0

    def test_cash_baseline(self):
        from scripts.scalp_backtest_runner import cash_baseline
        r = cash_baseline(initial_capital=10_000.0)
        assert r["total_pnl"] == 0.0
        assert r["total_pnl_pct"] == 0.0
        assert r["final_capital"] == 10_000.0
