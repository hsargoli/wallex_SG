"""Phase 2D-3: backtest must dispatch to range_strategy when strategy_mode='range'."""
from decimal import Decimal
from unittest.mock import MagicMock
import pytest
from app.domain.entities.candle import Candle


def _c(t, o, h, l, c, v="10"):
    return Candle(time=t, open=Decimal(str(o)), high=Decimal(str(h)),
                  low=Decimal(str(l)), close=Decimal(str(c)),
                  volume=Decimal(str(v)))


class _Sig:
    should_trade = True
    action = "buy"
    entry_price = 100.0
    take_profit = 110.0
    stop_loss = 95.0
    reason = "range"
    drop_pct = 0.0
    rsi = 25.0
    atr_pct = 1.0


class TestBacktestDispatch:
    def test_range_mode_uses_evaluate_entry_range(self, monkeypatch):
        """strategy_mode='range' → range fn called, watchlist fn NOT called."""
        import app.infrastructure.backtest.bot_backtest as bt
        from app.services.bots.scalp_master.config import ScalpMasterConfig

        calls = {"range": 0, "watchlist": 0}

        def fake_range(window, cfg):
            calls["range"] += 1
            return _Sig() if calls["range"] == 1 else None

        def fake_wl(*a, **k):
            calls["watchlist"] += 1
            return None

        monkeypatch.setattr(bt, "evaluate_entry_range", fake_range, raising=False)
        monkeypatch.setattr(bt, "evaluate_entry_with_watchlist", fake_wl)

        candles = [_c(i * 3600, 100, 101, 99, 100) for i in range(80)]
        cfg = ScalpMasterConfig(strategy_mode="range", warmup_candles=60)

        r = bt.run_scalp_backtest(
            candles, initial_capital=10_000.0, position_size_pct=100.0,
            fee_pct=0.0, slippage_pct=0.0, spread_pct=0.0, config=cfg,
        )
        assert calls["range"] > 0, "range fn must be called"
        assert calls["watchlist"] == 0, "watchlist fn must NOT be called"
        assert r["total_trades"] >= 1

    def test_dip_mode_uses_watchlist_or_dip(self, monkeypatch):
        """strategy_mode='dip' (default) → range fn NOT called."""
        import app.infrastructure.backtest.bot_backtest as bt
        from app.services.bots.scalp_master.config import ScalpMasterConfig

        calls = {"range": 0, "watchlist": 0}

        def fake_range(window, cfg):
            calls["range"] += 1
            return None

        def fake_wl(*a, **k):
            calls["watchlist"] += 1
            return None

        monkeypatch.setattr(bt, "evaluate_entry_range", fake_range, raising=False)
        monkeypatch.setattr(bt, "evaluate_entry_with_watchlist", fake_wl)

        candles = [_c(i * 3600, 100, 101, 99, 100) for i in range(80)]
        cfg = ScalpMasterConfig(strategy_mode="dip", warmup_candles=60)

        bt.run_scalp_backtest(
            candles, initial_capital=10_000.0, position_size_pct=100.0,
            fee_pct=0.0, slippage_pct=0.0, spread_pct=0.0, config=cfg,
        )
        assert calls["range"] == 0, "range fn must NOT be called in dip mode"
        assert calls["watchlist"] > 0
