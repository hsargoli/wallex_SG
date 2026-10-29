"""Phase 2A-2: backtest must apply slippage + spread (like real exchange)."""
from decimal import Decimal

import pytest
from app.domain.entities.candle import Candle


class _Sig:
    should_trade = True
    action = "buy"
    entry_price = 100.0
    take_profit = 110.0
    stop_loss = 95.0
    reason = "test"
    drop_pct = 3.0
    rsi = 35.0
    atr_pct = 1.0


def _candles(n=100):
    return [Candle(time=i * 3600, open=Decimal("100"), high=Decimal("101"),
                   low=Decimal("99"), close=Decimal("100"),
                   volume=Decimal("10")) for i in range(n)]


def _run_with(monkeypatch, slippage: float, spread: float) -> dict:
    import app.infrastructure.backtest.bot_backtest as bt
    state = {"n": 0}

    def fake_entry(window, cfg):
        state["n"] += 1
        return _Sig() if state["n"] == 1 else None

    def fake_exit(window, entry, sl, tp, held, cfg):
        return True, 105.0, "take_profit"

    monkeypatch.setattr(bt, "evaluate_entry", fake_entry)
    monkeypatch.setattr(bt, "evaluate_exit", fake_exit)
    return bt.run_scalp_backtest(
        _candles(), initial_capital=10_000.0, position_size_pct=100.0,
        fee_pct=0.2, slippage_pct=slippage, spread_pct=spread,
    )


class TestBacktestCosts:
    def test_slippage_and_spread_reduce_pnl(self, monkeypatch):
        clean = _run_with(monkeypatch, slippage=0.0, spread=0.0)
        costly = _run_with(monkeypatch, slippage=0.1, spread=0.05)
        assert clean["total_trades"] == 1
        assert costly["total_trades"] == 1
        assert costly["total_pnl"] < clean["total_pnl"]
        # Round-trip extra cost = 2*(0.1 + 0.025)% = 0.25% of ~10k ≈ 25 TMN
        diff = clean["total_pnl"] - costly["total_pnl"]
        assert 15.0 < diff < 40.0, f"unexpected diff: {diff}"

    def test_defaults_are_realistic(self):
        import inspect
        import app.infrastructure.backtest.bot_backtest as bt
        sig = inspect.signature(bt.run_scalp_backtest)
        assert "slippage_pct" in sig.parameters
        assert "spread_pct" in sig.parameters
        assert sig.parameters["slippage_pct"].default == 0.1
        assert sig.parameters["spread_pct"].default == 0.05
