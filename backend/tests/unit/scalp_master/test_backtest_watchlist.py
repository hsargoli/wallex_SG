"""Phase 2C-4: backtest must use watchlist when enabled."""
from decimal import Decimal
import pytest
from app.domain.entities.candle import Candle


def _c(t, o, h, l, c, v="100"):
    return Candle(time=t, open=Decimal(str(o)), high=Decimal(str(h)),
                  low=Decimal(str(l)), close=Decimal(str(c)),
                  volume=Decimal(str(v)))


def _flat_candles(n=100, top=200.0):
    return [_c(i * 3600, top, top + 0.5, top - 0.5, top) for i in range(n)]


class TestBacktestWatchlist:
    def test_crash_then_greens_triggers_entry(self):
        """Synthetic: 99 flat + 1 crash + 2 green → trade opened (watchlist confirm)."""
        from app.infrastructure.backtest.bot_backtest import run_scalp_backtest
        from app.services.bots.scalp_master.config import ScalpMasterConfig

        top = 200.0
        crash = top * 0.97
        candles = _flat_candles(99, top)
        candles.append(_c(99 * 3600, top, top + 0.5, crash - 1, crash))
        # 2 green candles
        g1 = crash + 2
        g2 = g1 + 2
        candles.append(_c(100 * 3600, crash, crash + 2, crash - 0.5, g1))
        candles.append(_c(101 * 3600, g1, g1 + 2, g1 - 0.5, g2))
        # 1 more to close
        candles.append(_c(102 * 3600, g2, g2 + 1, g2 - 1, g2 + 0.5))

        cfg = ScalpMasterConfig(watchlist_enabled=True)
        result = run_scalp_backtest(candles, initial_capital=10_000.0,
                                    position_size_pct=100.0, fee_pct=0.0,
                                    slippage_pct=0.0, spread_pct=0.0, config=cfg)
        assert result["total_trades"] >= 1, f"watchlist should trigger entry, got {result['total_trades']}"

    def test_crash_only_no_entry(self):
        """Crash without confirmation → no entry."""
        from app.infrastructure.backtest.bot_backtest import run_scalp_backtest
        from app.services.bots.scalp_master.config import ScalpMasterConfig

        top = 200.0
        crash = top * 0.97
        candles = _flat_candles(99, top)
        candles.append(_c(99 * 3600, top, top + 0.5, crash - 1, crash))
        # 10 flat candles after crash (no greens)
        for i in range(10):
            candles.append(_c((100 + i) * 3600, crash, crash + 0.5, crash - 0.5, crash))

        cfg = ScalpMasterConfig(watchlist_enabled=True)
        result = run_scalp_backtest(candles, initial_capital=10_000.0,
                                    position_size_pct=100.0, fee_pct=0.0,
                                    slippage_pct=0.0, spread_pct=0.0, config=cfg)
        assert result["total_trades"] == 0, f"no confirmation, no entry. Got {result['total_trades']}"
