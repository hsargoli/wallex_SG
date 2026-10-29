"""Phase 1B: report metrics from closed_trades."""
import pytest


class TestPaperReport:
    def test_computes_metrics(self):
        from scripts.scalp_paper_report import build_report
        trades = [
            {"pnl_net": 9000.0, "exit_reason": "take_profit"},
            {"pnl_net": -1800.0, "exit_reason": "stop_loss"},
            {"pnl_net": 6000.0, "exit_reason": "take_profit"},
            {"pnl_net": -4000.0, "exit_reason": "timeout"},
        ]
        r = build_report(trades, capital_start=300_000.0)
        assert r["total_trades"] == 4
        assert r["wins"] == 2
        assert r["losses"] == 2
        assert r["win_rate_pct"] == 50.0
        assert r["avg_win"] == 7500.0
        assert r["avg_loss"] == -2900.0
        assert r["total_pnl"] == 9200.0
        assert r["best_trade"] == 9000.0
        assert r["worst_trade"] == -4000.0
        assert r["by_reason"]["take_profit"] == 2

    def test_empty(self):
        from scripts.scalp_paper_report import build_report
        r = build_report([], capital_start=300_000.0)
        assert r["total_trades"] == 0
        assert r["win_rate_pct"] == 0.0
        assert r["total_pnl"] == 0.0

    def test_max_drawdown(self):
        from scripts.scalp_paper_report import build_report
        trades = [
            {"pnl_net": 10_000.0, "exit_reason": "take_profit"},
            {"pnl_net": -15_000.0, "exit_reason": "stop_loss"},
            {"pnl_net": 10_000.0, "exit_reason": "take_profit"},
        ]
        r = build_report(trades, capital_start=300_000.0)
        assert r["max_drawdown_pct"] == pytest.approx(-4.8387, rel=1e-3)
