"""Phase 2D-2: range strategy (ADX<20 + RSI<30 + Volume spike + Green body)."""
from decimal import Decimal
import pytest
from app.domain.entities.candle import Candle
from app.services.bots.scalp_master.config import ScalpMasterConfig


def _c(t, o, h, l, c, v="10"):
    return Candle(time=t, open=Decimal(str(o)), high=Decimal(str(h)),
                  low=Decimal(str(l)), close=Decimal(str(c)),
                  volume=Decimal(str(v)))


def _base_candles(n=60):
    """60 flat candles — for warmup."""
    return [_c(i*3600, 100, 101, 99, 100) for i in range(n)]


def _mock_indicators(monkeypatch, adx_v=15.0, rsi_v=25.0, vol_avg=100.0):
    import app.services.bots.scalp_master.strategy as s
    monkeypatch.setattr(s, "adx", lambda c, p=14: [adx_v] * len(c))
    monkeypatch.setattr(s, "rsi", lambda c, p=14: [rsi_v] * len(c))
    monkeypatch.setattr(s, "volume_sma", lambda c, p=20: [vol_avg] * len(c))


def _green_last(candles, body_pct=1.0, vol="250"):
    """Replace last candle with green candle + volume spike."""
    last = candles[-1]
    new_c = float(last.open) * (1 + body_pct / 100)
    candles[-1] = _c(int(last.time), float(last.open), new_c + 0.5, float(last.open) - 0.5, new_c, v=vol)
    return candles


class TestRangeStrategy:
    def test_high_adx_blocks_entry(self, monkeypatch):
        """ADX > 20 → no trade (market trending, not range)."""
        from app.services.bots.scalp_master.strategy import evaluate_entry_range
        cfg = ScalpMasterConfig(strategy_mode="range", range_adx_max=20.0)
        _mock_indicators(monkeypatch, adx_v=30.0)
        candles = _green_last(_base_candles(), body_pct=1.0, vol="250")
        assert evaluate_entry_range(candles, cfg) is None

    def test_high_rsi_blocks_entry(self, monkeypatch):
        """RSI > 30 → no trade (not oversold)."""
        from app.services.bots.scalp_master.strategy import evaluate_entry_range
        cfg = ScalpMasterConfig(strategy_mode="range", range_rsi_max=30.0)
        _mock_indicators(monkeypatch, adx_v=15.0, rsi_v=45.0)
        candles = _green_last(_base_candles(), body_pct=1.0, vol="250")
        assert evaluate_entry_range(candles, cfg) is None

    def test_no_volume_spike_blocks(self, monkeypatch):
        """Volume < 2x avg → no trade."""
        from app.services.bots.scalp_master.strategy import evaluate_entry_range
        cfg = ScalpMasterConfig(strategy_mode="range", range_volume_mult=2.0)
        _mock_indicators(monkeypatch, adx_v=15.0, rsi_v=25.0, vol_avg=100.0)
        # volume = 150 (< 2x100)
        candles = _green_last(_base_candles(), body_pct=1.0, vol="150")
        assert evaluate_entry_range(candles, cfg) is None

    def test_small_body_blocks(self, monkeypatch):
        """Green body < 0.5% → no trade."""
        from app.services.bots.scalp_master.strategy import evaluate_entry_range
        cfg = ScalpMasterConfig(strategy_mode="range", range_green_body_pct=0.5)
        _mock_indicators(monkeypatch, adx_v=15.0, rsi_v=25.0)
        # body 0.1% (< 0.5%)
        candles = _green_last(_base_candles(), body_pct=0.1, vol="250")
        assert evaluate_entry_range(candles, cfg) is None

    def test_all_gates_pass_triggers_entry(self, monkeypatch):
        """ADX<20 + RSI<30 + Vol spike + Green body ≥0.5% → trade."""
        from app.services.bots.scalp_master.strategy import evaluate_entry_range
        cfg = ScalpMasterConfig(strategy_mode="range")
        _mock_indicators(monkeypatch, adx_v=15.0, rsi_v=25.0, vol_avg=100.0)
        candles = _green_last(_base_candles(), body_pct=1.0, vol="250")
        sig = evaluate_entry_range(candles, cfg)
        assert sig is not None
        assert sig.should_trade is True
        assert sig.action == "buy"

    def test_tp_sl_ratio_is_2_to_1(self, monkeypatch):
        """TP distance = 2x SL distance (ATR-based R/R)."""
        from app.services.bots.scalp_master.strategy import evaluate_entry_range
        cfg = ScalpMasterConfig(strategy_mode="range")
        _mock_indicators(monkeypatch, adx_v=15.0, rsi_v=25.0, vol_avg=100.0)
        candles = _green_last(_base_candles(), body_pct=1.0, vol="250")
        sig = evaluate_entry_range(candles, cfg)
        assert sig is not None
        entry = sig.entry_price
        sl_dist = entry - sig.stop_loss
        tp_dist = sig.take_profit - entry
        if sl_dist > 0:
            ratio = tp_dist / sl_dist
            # 3.0 ATR / 1.5 ATR = 2.0
            assert 1.8 < ratio < 2.2, f"R/R should be ~2:1, got {ratio:.2f}"
