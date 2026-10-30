"""Outcome analysis + signal decision (sarv_tiger analyzer).

Given top-K similar historical windows, compute:
  - direction probability (p_up_*) for 24h, 72h, 168h
  - hit-flag rates (p_hit_tp_168h, p_hit_sl_168h)
  - average returns (avg_return_*)

Then decide: signal = "long" or "none", based on mode + baseline-relative
thresholds (AP-32: no absolute thresholds).

Modes:
    "delta" (default): direction AND relative hit flags (most complete)
    "alpha"           : relative hit flag only
    "gamma"           : direction only

Baseline (compute_baseline): the global rates across the entire history.
Used for relative comparison (e.g., p_hit_tp_top_k > baseline × 1.5).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.services.bots.sarv_tiger.analyzer.analyzer_config import (
    AnalyzerConfig,
)

EPS = 1e-9


@dataclass(slots=True)
class OutcomeAnalysis:
    k: int
    p_up_24h: float
    p_up_72h: float
    p_up_168h: float
    p_hit_tp_168h: float
    p_hit_sl_168h: float
    avg_return_24h: float
    avg_return_72h: float
    avg_return_168h: float
    signal: str          # "long" | "none"
    confidence: float    # 0.0 .. 1.0


def compute_baseline(windows: list[dict[str, Any]]) -> dict[str, float]:
    """Compute global baseline rates from the full history archive.

    Returns dict with keys:
        p_up_168h, p_hit_tp_168h, p_hit_sl_168h

    Empty input → all zeros.
    """
    if not windows:
        return {
            "p_up_168h": 0.0,
            "p_hit_tp_168h": 0.0,
            "p_hit_sl_168h": 0.0,
        }

    n = len(windows)
    return {
        "p_up_168h": sum(1 for w in windows if w.get("outcome_168h", 0.0) > 0) / n,
        "p_hit_tp_168h": sum(1 for w in windows if w.get("hit_tp_168h", False)) / n,
        "p_hit_sl_168h": sum(1 for w in windows if w.get("hit_sl_168h", False)) / n,
    }


def analyze_outcomes(
    windows: list[dict[str, Any]],
    cfg: AnalyzerConfig,
    baseline: dict[str, float],
) -> OutcomeAnalysis:
    """Analyze top-K similar windows and decide signal.

    Args:
        windows: list of window dicts (from history). Extra keys ignored.
        cfg: AnalyzerConfig with thresholds and signal_mode.
        baseline: output of compute_baseline on the full history.

    Returns:
        OutcomeAnalysis with all rates and the decision.
    """
    k = len(windows)
    if k == 0:
        return OutcomeAnalysis(
            k=0,
            p_up_24h=0.0, p_up_72h=0.0, p_up_168h=0.0,
            p_hit_tp_168h=0.0, p_hit_sl_168h=0.0,
            avg_return_24h=0.0, avg_return_72h=0.0, avg_return_168h=0.0,
            signal="none", confidence=0.0,
        )

    p_up_24h = sum(1 for w in windows if w.get("outcome_24h", 0.0) > 0) / k
    p_up_72h = sum(1 for w in windows if w.get("outcome_72h", 0.0) > 0) / k
    p_up_168h = sum(1 for w in windows if w.get("outcome_168h", 0.0) > 0) / k

    p_hit_tp_168h = sum(1 for w in windows if w.get("hit_tp_168h", False)) / k
    p_hit_sl_168h = sum(1 for w in windows if w.get("hit_sl_168h", False)) / k

    avg_return_24h = sum(w.get("outcome_24h", 0.0) for w in windows) / k
    avg_return_72h = sum(w.get("outcome_72h", 0.0) for w in windows) / k
    avg_return_168h = sum(w.get("outcome_168h", 0.0) for w in windows) / k

    baseline_up = baseline.get("p_up_168h", 0.0)
    baseline_tp = baseline.get("p_hit_tp_168h", 0.0)

    # Direction gate: beats baseline by margin AND above floor
    direction_ok = (
        p_up_168h > baseline_up * cfg.p_up_mult
        and p_up_168h > cfg.p_up_floor
    )
    # Hit-flag gate: TP rate beats baseline by margin, SL rate not too high
    hit_ok = (
        p_hit_tp_168h > baseline_tp * cfg.p_hit_tp_mult
        and p_hit_sl_168h < cfg.p_hit_sl_max
    )
    # Return gate (only in delta mode)
    return_ok = avg_return_168h > cfg.avg_return_168h_min

    mode = cfg.signal_mode
    if mode == "gamma":
        signal_long = direction_ok
    elif mode == "alpha":
        signal_long = hit_ok
    else:  # "delta" or any unknown → most complete
        signal_long = direction_ok and hit_ok and return_ok

    if signal_long:
        # Confidence: how "good" the signal is, in [0, 1]
        confidence = min(1.0, max(0.0, p_up_168h * 0.6 + p_hit_tp_168h * 0.4))
        return OutcomeAnalysis(
            k=k,
            p_up_24h=p_up_24h, p_up_72h=p_up_72h, p_up_168h=p_up_168h,
            p_hit_tp_168h=p_hit_tp_168h, p_hit_sl_168h=p_hit_sl_168h,
            avg_return_24h=avg_return_24h,
            avg_return_72h=avg_return_72h,
            avg_return_168h=avg_return_168h,
            signal="long",
            confidence=confidence,
        )

    return OutcomeAnalysis(
        k=k,
        p_up_24h=p_up_24h, p_up_72h=p_up_72h, p_up_168h=p_up_168h,
        p_hit_tp_168h=p_hit_tp_168h, p_hit_sl_168h=p_hit_sl_168h,
        avg_return_24h=avg_return_24h,
        avg_return_72h=avg_return_72h,
        avg_return_168h=avg_return_168h,
        signal="none",
        confidence=0.0,
    )
