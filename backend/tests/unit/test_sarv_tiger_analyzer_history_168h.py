"""SarvTiger analyzer — 168h hit flags (TDD RED for Phase 3.7).

Rationale (from DAILY_2026-10-30 analysis):
  - TP=8ATR within 24h: p=0.61% (never fires)
  - sarv_tiger is swing (7 trades/year, weeks per trade)
  - 168h (7 days) horizon is the realistic one for hit flags
  - Direction (p_up_168h) is primary signal; hit flags are secondary
"""
import pytest
from decimal import Decimal
from app.domain.entities.candle import Candle
from app.services.bots.sarv_tiger.analyzer.history import (
    HistoricalWindow,
    build_windows,
    HORIZON_168H,
)


def _c(ts, o, h, l, c, v="100"):
    return Candle(
        time=ts, open=Decimal(str(o)), high=Decimal(str(h)),
        low=Decimal(str(l)), close=Decimal(str(c)),
        volume=Decimal(str(v)),
    )


def _flat_then_jump(n=200, jump_at=100, jump_pct=0.10):
    """Flat around 100, then +jump_pct, then continue flat."""
    out = []
    for i in range(n):
        base = 100.0 * (1.0 + jump_pct) if i >= jump_at else 100.0
        out.append(_c(
            i * 14400,
            base,
            base + 0.5,
            base - 0.5,
            base,
        ))
    return out


class TestHistoricalWindow168hFields:
    def test_fields_exist(self):
        w = HistoricalWindow(
            window_start_ts=0, window_end_ts=0,
            features=[0.0] * 10,
            outcome_24h=0.0, outcome_72h=0.0, outcome_168h=0.0,
            hit_sl_24h=False, hit_tp_24h=False,
            hit_sl_168h=False, hit_tp_168h=False,
        )
        assert w.hit_sl_168h is False
        assert w.hit_tp_168h is False

    def test_to_dict_includes_168h(self):
        w = HistoricalWindow(
            window_start_ts=0, window_end_ts=0,
            features=[0.0] * 10,
            outcome_24h=0.0, outcome_72h=0.0, outcome_168h=0.0,
            hit_sl_24h=False, hit_tp_24h=False,
            hit_sl_168h=True, hit_tp_168h=True,
        )
        d = w.to_dict()
        assert "hit_sl_168h" in d
        assert "hit_tp_168h" in d
        assert d["hit_sl_168h"] is True
        assert d["hit_tp_168h"] is True

    def test_from_dict_round_trip(self):
        d = {
            "window_start_ts": 100, "window_end_ts": 200,
            "features": [0.1] * 10,
            "outcome_24h": 0.01, "outcome_72h": 0.02, "outcome_168h": 0.03,
            "hit_sl_24h": True, "hit_tp_24h": False,
            "hit_sl_168h": False, "hit_tp_168h": True,
        }
        w = HistoricalWindow.from_dict(d)
        assert w.hit_sl_168h is False
        assert w.hit_tp_168h is True


class TestBuildWindows168h:
    def test_hit_tp_168h_when_jump_after_window(self):
        """Window ends before jump; TP (8 ATR) hit within 168h."""
        candles = _flat_then_jump(n=200, jump_at=100, jump_pct=0.10)
        windows = build_windows(candles)
        # jump at idx=100; 168h future = [end_idx+1, end_idx+42].
        # So end_idx in [58, 99] sees the jump. Check at least one.
        found = False
        for w in windows:
            end_idx = w.window_end_ts // 14400
            if 58 <= end_idx <= 99 and w.hit_tp_168h:
                found = True
                break
        assert found, "no window in [58,99] with hit_tp_168h=True"

    def test_hit_sl_168h_when_drop_after_window(self):
        """Window ends before drop; SL (1.2 ATR) hit within 168h."""
        candles = _flat_then_jump(n=200, jump_at=100, jump_pct=-0.10)
        windows = build_windows(candles)
        found = False
        for w in windows:
            end_idx = w.window_end_ts // 14400
            if 58 <= end_idx <= 99 and w.hit_sl_168h:
                found = True
                break
        assert found, "no window in [58,99] with hit_sl_168h=True"

    def test_no_hit_if_jump_too_far(self):
        """If jump is far beyond 168h window, no hit recorded at that horizon."""
        candles = _flat_then_jump(n=300, jump_at=250, jump_pct=0.10)
        windows = build_windows(candles)
        # Windows ending well before jump (end_idx < 100) should not have hit_tp_168h
        early = [w for w in windows if w.window_end_ts // 14400 < 100]
        assert early
        for w in early:
            assert w.hit_tp_168h is False, (
                f"window at idx {w.window_end_ts//14400} has hit_tp_168h=True, "
                f"but jump is at idx 250 (too far)"
            )
