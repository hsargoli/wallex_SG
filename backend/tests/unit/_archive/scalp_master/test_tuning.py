"""Phase 2B-2: walk-forward tuning — no look-ahead, pick best on train, test on test."""
from decimal import Decimal
from app.domain.entities.candle import Candle


def _c(t, o, h, l, c, v="100"):
    return Candle(time=t, open=Decimal(str(o)), high=Decimal(str(h)),
                  low=Decimal(str(l)), close=Decimal(str(c)),
                  volume=Decimal(str(v)))


def _flat_candles(n=200):
    """Consolidating market — no entries expected."""
    return [_c(i*3600, 100, 100.5, 99.5, 100) for i in range(n)]


class TestWalkForward:
    def test_split_periods(self):
        from scripts.scalp_tuning import split_walk_forward
        folds = split_walk_forward(
            start_ts=0, end_ts=1000, train_size=600, test_size=200,
        )
        # 0-600 train / 600-800 test  →  then 200-800 train / 800-1000 test
        assert len(folds) == 2
        assert folds[0]["train"] == (0, 600)
        assert folds[0]["test"] == (600, 800)
        assert folds[1]["train"] == (200, 800)
        assert folds[1]["test"] == (800, 1000)

    def test_parameter_grid(self):
        from scripts.scalp_tuning import default_grid
        grid = default_grid()
        assert "drop_threshold_pct" in grid
        assert "rsi_min" in grid
        assert "rsi_max" in grid
        assert "sl_atr_mult" in grid
        assert "tp_atr_mult" in grid
        assert "trend_ema_gap_pct" in grid
        total = 1
        for k, vals in grid.items():
            assert len(vals) > 0, f"{k} must have values"
            total *= len(vals)
        assert total < 500, f"grid too large: {total}"

    def test_apply_params_returns_config(self):
        from scripts.scalp_tuning import apply_params
        from app.services.bots.scalp_master.config import ScalpMasterConfig
        base = ScalpMasterConfig()
        cfg = apply_params(base, {"drop_threshold_pct": 3.0, "rsi_min": 20.0})
        assert cfg.drop_threshold_pct == 3.0
        assert cfg.rsi_min == 20.0
        assert cfg.rsi_max == base.rsi_max  # unchanged
