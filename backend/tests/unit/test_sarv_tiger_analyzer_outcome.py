"""SarvTiger analyzer — outcome analysis + signal decision (TDD RED first).

All thresholds are RELATIVE to baseline (AP-32):
    baseline_p_up_168h      computed from full history
    baseline_p_hit_tp_168h  computed from full history
Never hardcode 0.55 or 0.5 — those are absolute and regime-blind.
"""
import pytest
import numpy as np
from app.services.bots.sarv_tiger.analyzer.analyzer_config import (
    AnalyzerConfig,
)
from app.services.bots.sarv_tiger.analyzer.outcome import (
    OutcomeAnalysis,
    analyze_outcomes,
    compute_baseline,
)


def _w(p_up=0.5, p_tp=0.1, p_sl=0.4, avg_168=0.0):
    """Minimal window dict for outcome tests."""
    # hit_tp_168h is a bool; emulate as Bernoulli via repeated windows
    return {
        "outcome_24h": 0.0,
        "outcome_72h": 0.0,
        "outcome_168h": avg_168,
        "hit_tp_168h": p_tp > 0.5,
        "hit_sl_168h": p_sl > 0.5,
    }


class TestBaseline:
    def test_empty_returns_zeros(self):
        bl = compute_baseline([])
        assert bl["p_up_168h"] == 0.0
        assert bl["p_hit_tp_168h"] == 0.0

    def test_counts_correctly(self):
        windows = [
            {"outcome_168h": 0.05, "hit_tp_168h": True,  "hit_sl_168h": False},
            {"outcome_168h": -0.02, "hit_tp_168h": False, "hit_sl_168h": True},
            {"outcome_168h": 0.03, "hit_tp_168h": True,  "hit_sl_168h": False},
            {"outcome_168h": 0.01, "hit_tp_168h": False, "hit_sl_168h": False},
        ]
        bl = compute_baseline(windows)
        assert bl["p_up_168h"] == 0.75
        assert bl["p_hit_tp_168h"] == 0.5
        assert bl["p_hit_sl_168h"] == 0.25


class TestAnalyzeOutcomes:
    def test_empty_returns_none_signal(self):
        cfg = AnalyzerConfig()
        result = analyze_outcomes([], cfg, baseline={"p_up_168h": 0.5, "p_hit_tp_168h": 0.1})
        assert result.signal == "none"
        assert result.k == 0

    def test_strong_bullish_windows(self):
        """All top-K windows up strongly, many hit TP → long."""
        cfg = AnalyzerConfig()
        windows = [
            {"outcome_168h": 0.05, "hit_tp_168h": True,  "hit_sl_168h": False, "outcome_24h": 0.02, "outcome_72h": 0.04},
        ] * 50
        baseline = {"p_up_168h": 0.5, "p_hit_tp_168h": 0.08}
        result = analyze_outcomes(windows, cfg, baseline=baseline)
        assert result.signal == "long"
        assert result.p_up_168h == 1.0
        assert result.p_hit_tp_168h == 1.0

    def test_bearish_windows_no_signal(self):
        cfg = AnalyzerConfig()
        windows = [
            {"outcome_168h": -0.04, "hit_tp_168h": False, "hit_sl_168h": True, "outcome_24h": -0.01, "outcome_72h": -0.03},
        ] * 50
        baseline = {"p_up_168h": 0.5, "p_hit_tp_168h": 0.08}
        result = analyze_outcomes(windows, cfg, baseline=baseline)
        assert result.signal == "none"

    def test_mixed_windows_no_signal(self):
        """50/50 up/down, baseline-level → none."""
        cfg = AnalyzerConfig()
        windows = []
        for i in range(100):
            windows.append({
                "outcome_168h": 0.01 if i % 2 == 0 else -0.01,
                "hit_tp_168h": i % 5 == 0,
                "hit_sl_168h": False,
                "outcome_24h": 0.0, "outcome_72h": 0.0,
            })
        baseline = {"p_up_168h": 0.5, "p_hit_tp_168h": 0.1}
        result = analyze_outcomes(windows, cfg, baseline=baseline)
        assert result.signal == "none"

    def test_confidence_in_range(self):
        cfg = AnalyzerConfig()
        windows = [{"outcome_168h": 0.05, "hit_tp_168h": True, "hit_sl_168h": False,
                    "outcome_24h": 0.0, "outcome_72h": 0.0}] * 50
        baseline = {"p_up_168h": 0.5, "p_hit_tp_168h": 0.08}
        result = analyze_outcomes(windows, cfg, baseline=baseline)
        assert 0.0 <= result.confidence <= 1.0


class TestRelativeThresholds:
    def test_slightly_above_baseline_no_signal(self):
        """p_up=55% vs baseline=50% → not enough (need ×1.1)."""
        cfg = AnalyzerConfig()
        windows = []
        for i in range(100):
            windows.append({
                "outcome_168h": 0.01 if i < 55 else -0.01,
                "hit_tp_168h": i < 5,
                "hit_sl_168h": False,
                "outcome_24h": 0.0, "outcome_72h": 0.0,
            })
        baseline = {"p_up_168h": 0.5, "p_hit_tp_168h": 0.1}
        result = analyze_outcomes(windows, cfg, baseline=baseline)
        assert result.signal == "none"

    def test_well_above_baseline_signal(self):
        """p_up=80% vs baseline=50% (×1.6) → long."""
        cfg = AnalyzerConfig()
        windows = []
        for i in range(100):
            windows.append({
                "outcome_168h": 0.02 if i < 80 else -0.01,
                "hit_tp_168h": i < 20,  # 20% vs 10% baseline = ×2
                "hit_sl_168h": False,
                "outcome_24h": 0.0, "outcome_72h": 0.0,
            })
        baseline = {"p_up_168h": 0.5, "p_hit_tp_168h": 0.1}
        result = analyze_outcomes(windows, cfg, baseline=baseline)
        assert result.signal == "long"


class TestSignalModes:
    def test_gamma_mode_direction_only(self):
        cfg = AnalyzerConfig(signal_mode="gamma")
        windows = [{"outcome_168h": 0.05, "hit_tp_168h": False, "hit_sl_168h": True,
                    "outcome_24h": 0.0, "outcome_72h": 0.0}] * 50
        baseline = {"p_up_168h": 0.5, "p_hit_tp_168h": 0.1}
        result = analyze_outcomes(windows, cfg, baseline=baseline)
        # gamma ignores hit flags; direction is 100% up → long
        assert result.signal == "long"

    def test_alpha_mode_baseline_multiple(self):
        cfg = AnalyzerConfig(signal_mode="alpha", p_hit_tp_mult=1.5)
        windows = [{"outcome_168h": 0.01, "hit_tp_168h": True, "hit_sl_168h": False,
                    "outcome_24h": 0.0, "outcome_72h": 0.0}] * 50
        baseline = {"p_up_168h": 0.5, "p_hit_tp_168h": 0.1}
        result = analyze_outcomes(windows, cfg, baseline=baseline)
        # p_tp=1.0 > 0.1×1.5 → long
        assert result.signal == "long"


class TestOutcomeAnalysisDataclass:
    def test_fields(self):
        o = OutcomeAnalysis(
            k=50, p_up_24h=0.6, p_up_72h=0.62, p_up_168h=0.65,
            p_hit_tp_168h=0.15, p_hit_sl_168h=0.7,
            avg_return_24h=0.01, avg_return_72h=0.02, avg_return_168h=0.03,
            signal="long", confidence=0.4,
        )
        assert o.signal == "long"
        assert o.k == 50
        assert o.confidence == 0.4
