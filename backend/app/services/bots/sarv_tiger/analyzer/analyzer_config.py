"""Analyzer configuration — thresholds and mode (NEVER hardcode).

All p_* thresholds are RELATIVE (multiples of baseline), not absolute.
This is critical (AP-32): absolute thresholds are regime-blind and will
silently stop firing when the regime shifts.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class AnalyzerConfig:
    # Number of similar historical windows to analyze
    k: int = 50

    # Signal decision mode:
    #   "delta" — direction + relative hit flags (default, most complete)
    #   "alpha" — relative hit flag only (p_hit_tp × mult)
    #   "gamma" — direction only (p_up vs baseline × mult)
    #   "none"  — CONTROL: always long (bypass analyzer)
    signal_mode: str = "delta"

    # Relative thresholds (multiples of baseline)
    p_up_mult: float = 1.1           # need p_up > baseline × 1.1
    p_hit_tp_mult: float = 1.5       # need p_tp > baseline × 1.5
    p_hit_sl_max: float = 0.85       # skip if p_sl > 0.85 (too many stops)

    # Direction floor: p_up_168h must be above this regardless of baseline
    p_up_floor: float = 0.55

    # Minimum avg return to consider entry
    avg_return_168h_min: float = 0.005  # +0.5%
