"""Similarity search for sarv_tiger analyzer.

Given the current window's feature vector and a history archive, find the
top-K historical windows most similar (cosine) — but only those whose
168h outcome was already known at the query time.

Leakage rule (CRITICAL):
    A history window ending at ts_e is usable at query time T only if
        ts_e + HORIZON_168H_SECONDS < T
    Otherwise, its outcome_168h was not yet known when the query was made.

Guard:
    If fewer than MIN_HISTORY_FOR_SIGNAL windows are usable, return empty
    arrays (statistics on <1000 windows is not reliable).

Performance:
    Vectorized with numpy (matmul + norms + argpartition). Designed for
    backtests with ~10k history windows: < 10ms per query.
"""
from __future__ import annotations

import numpy as np

MIN_HISTORY_FOR_SIGNAL = 1000
HORIZON_168H_SECONDS = 42 * 4 * 3600  # 604800s = 7 days
EPS = 1e-9


def find_similar(
    query: np.ndarray,
    history: list[dict],
    k: int,
    current_ts: int,
) -> tuple[np.ndarray, np.ndarray]:
    """Return (indices, similarities) of top-K similar usable windows.

    Args:
        query: 1D feature vector (N_FEATURES,).
        history: list of dicts, each with keys 'features' and
            'window_end_ts'. Extra keys ignored.
        k: desired number of neighbors.
        current_ts: query time (seconds). Used for leakage-safe filtering.

    Returns:
        (indices, similarities):
          - indices: int array of positions in `history` (not filtered array).
          - similarities: float array, non-increasing.
        Both empty if history is empty or fewer than MIN_HISTORY_FOR_SIGNAL
        windows are usable.

    Note:
        Similarity is cosine (range [-1, 1]). Exact duplicates → 1.0.
    """
    if not history:
        return np.array([], dtype=int), np.array([], dtype=float)

    end_ts = np.array([h["window_end_ts"] for h in history], dtype=float)
    usable_mask = (end_ts + HORIZON_168H_SECONDS) < float(current_ts)
    usable_idx = np.where(usable_mask)[0]

    if len(usable_idx) < MIN_HISTORY_FOR_SIGNAL:
        return np.array([], dtype=int), np.array([], dtype=float)

    full_mat = np.array([h["features"] for h in history], dtype=float)
    mat = full_mat[usable_idx]

    query_norm = float(np.linalg.norm(query)) + EPS
    row_norms = np.linalg.norm(mat, axis=1) + EPS
    dots = mat @ query
    sims = dots / (row_norms * query_norm)

    k_eff = min(int(k), len(sims))
    if k_eff <= 0:
        return np.array([], dtype=int), np.array([], dtype=float)

    if k_eff < len(sims):
        top_local = np.argpartition(-sims, k_eff - 1)[:k_eff]
    else:
        top_local = np.arange(len(sims))

    order = np.argsort(-sims[top_local])
    top_local = top_local[order]

    return usable_idx[top_local].astype(int), sims[top_local]
