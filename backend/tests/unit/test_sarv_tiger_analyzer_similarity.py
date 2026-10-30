"""SarvTiger analyzer — similarity search (TDD RED first).

Requirements from Di Koir:
  - Vectorized (numpy) for backtest speed
  - Leakage-safe: exclude windows whose 168h outcome wasn't known at T
  - MIN_HISTORY_FOR_SIGNAL guard (1000 windows)
"""
import numpy as np
import pytest
from app.services.bots.sarv_tiger.analyzer.similarity import (
    find_similar,
    MIN_HISTORY_FOR_SIGNAL,
    HORIZON_168H_SECONDS,
)


def _mk_windows(n, features_list, end_ts_list):
    """Helper: minimal window dicts (only fields similarity needs)."""
    return [
        {
            "features": features_list[i],
            "window_end_ts": end_ts_list[i],
        }
        for i in range(n)
    ]


class TestFindSimilar:
    def test_identical_pattern_top_score(self, monkeypatch):
        """A query identical to one history window must rank it #1.

        Note: cosine is scale-invariant, so we make target's DIRECTION
        unique (not just a multiple of [1]*10).
        """
        import app.services.bots.sarv_tiger.analyzer.similarity as sim_mod
        monkeypatch.setattr(sim_mod, "MIN_HISTORY_FOR_SIGNAL", 0)
        target = [0.5, 0.3, 0.7, 0.1, 0.9, 0.2, 0.8, 0.4, 0.6, 0.0]
        hist = _mk_windows(
            n=10,
            features_list=[
                target if i == 5 else [float(i + 1)] * 10
                for i in range(10)
            ],
            end_ts_list=[i * 14400 for i in range(10)],
        )
        query = np.array(target)
        current_ts = 10 * 14400 + HORIZON_168H_SECONDS + 1
        idx, sims = find_similar(query, hist, k=3, current_ts=current_ts)
        assert idx[0] == 5
        assert sims[0] > 0.999

    def test_ranking_monotonic(self):
        """Returned sims must be non-increasing."""
        hist = _mk_windows(
            n=20,
            features_list=[[0.05 * i] * 10 for i in range(20)],
            end_ts_list=[i * 14400 for i in range(20)],
        )
        query = np.array([0.4] * 10)
        current_ts = 20 * 14400 + HORIZON_168H_SECONDS + 1
        idx, sims = find_similar(query, hist, k=5, current_ts=current_ts)
        assert all(sims[i] >= sims[i + 1] for i in range(len(sims) - 1))

    def test_k_parameter(self, monkeypatch):
        import app.services.bots.sarv_tiger.analyzer.similarity as sim_mod
        monkeypatch.setattr(sim_mod, "MIN_HISTORY_FOR_SIGNAL", 0)
        hist = _mk_windows(
            n=100,
            features_list=[[0.01 * i] * 10 for i in range(100)],
            end_ts_list=[i * 14400 for i in range(100)],
        )
        query = np.array([0.5] * 10)
        current_ts = 100 * 14400 + HORIZON_168H_SECONDS + 1
        for k in (10, 50):
            idx, sims = find_similar(query, hist, k=k, current_ts=current_ts)
            assert len(idx) == k


class TestLeakageSafety:
    def test_excludes_future_windows(self):
        """A window ending at or after current_ts must be excluded."""
        # 5 windows, last 2 end after current_ts
        hist = _mk_windows(
            n=5,
            features_list=[[float(i)] * 10 for i in range(5)],
            end_ts_list=[100, 200, 300, 400, 500],
        )
        query = np.array([0.0] * 10)
        current_ts = 350
        idx, sims = find_similar(query, hist, k=10, current_ts=current_ts)
        # Only windows with end_ts + 168h < 350 are usable.
        # end_ts + 604800 < 350 → none usable (all end_ts > 350 - 604800)
        # Wait: 100 + 604800 = 604900 > 350 → none
        # This means: no history can be used at early T. Correct (leakage).
        assert len(idx) == 0

    def test_uses_168h_outcome_cutoff(self, monkeypatch):
        """Windows whose 168h outcome isn't known yet must be excluded."""
        import app.services.bots.sarv_tiger.analyzer.similarity as sim_mod
        monkeypatch.setattr(sim_mod, "MIN_HISTORY_FOR_SIGNAL", 0)
        # Use large ts so cutoff matters
        base_ts = 1_000_000_000
        hist = _mk_windows(
            n=5,
            features_list=[[float(i)] * 10 for i in range(5)],
            end_ts_list=[
                base_ts,
                base_ts + 14400,
                base_ts + 28800,
                base_ts + 43200,
                base_ts + 57600,
            ],
        )
        query = np.array([2.0] * 10)
        # current_ts is just after window 2's end + 168h
        current_ts = base_ts + 28800 + HORIZON_168H_SECONDS + 1
        idx, sims = find_similar(query, hist, k=10, current_ts=current_ts)
        # Usable: windows 0, 1, 2 (their 168h outcome known at current_ts)
        # Windows 3, 4 excluded (future)
        assert len(idx) == 3
        assert set(idx) == {0, 1, 2}


class TestMinHistoryGuard:
    def test_returns_empty_below_min(self):
        """Below MIN_HISTORY_FOR_SIGNAL usable windows → return empty arrays."""
        n = MIN_HISTORY_FOR_SIGNAL - 1
        hist = _mk_windows(
            n=n,
            features_list=[[0.0] * 10] * n,
            end_ts_list=[i * 14400 for i in range(n)],
        )
        query = np.array([0.0] * 10)
        current_ts = n * 14400 + HORIZON_168H_SECONDS + 1
        idx, sims = find_similar(query, hist, k=10, current_ts=current_ts)
        assert len(idx) == 0

    def test_works_at_min(self):
        n = MIN_HISTORY_FOR_SIGNAL
        hist = _mk_windows(
            n=n,
            features_list=[[0.0] * 10] * n,
            end_ts_list=[i * 14400 for i in range(n)],
        )
        query = np.array([0.0] * 10)
        current_ts = n * 14400 + HORIZON_168H_SECONDS + 1
        idx, sims = find_similar(query, hist, k=10, current_ts=current_ts)
        assert len(idx) == 10


class TestVectorization:
    def test_speed_under_10ms(self):
        """10k history × 10 features → must be < 10ms (numpy vectorized)."""
        import time
        n = 10_000
        hist = _mk_windows(
            n=n,
            features_list=[list(np.random.randn(10)) for _ in range(n)],
            end_ts_list=[i * 14400 for i in range(n)],
        )
        query = np.random.randn(10)
        current_ts = n * 14400 + HORIZON_168H_SECONDS + 1
        t0 = time.perf_counter()
        find_similar(query, hist, k=50, current_ts=current_ts)
        elapsed_ms = (time.perf_counter() - t0) * 1000
        assert elapsed_ms < 10.0, f"too slow: {elapsed_ms:.1f}ms"


class TestEdgeCases:
    def test_empty_history_returns_empty(self):
        query = np.array([0.0] * 10)
        idx, sims = find_similar(query, [], k=10, current_ts=10_000_000_000)
        assert len(idx) == 0

    def test_k_larger_than_usable(self):
        hist = _mk_windows(
            n=3,
            features_list=[[0.0] * 10] * 3,
            end_ts_list=[i * 14400 for i in range(3)],
        )
        query = np.array([0.0] * 10)
        current_ts = 3 * 14400 + HORIZON_168H_SECONDS + 1
        # MIN_HISTORY guard won't trigger if we monkeypatch
        import app.services.bots.sarv_tiger.analyzer.similarity as sim_mod
        original = sim_mod.MIN_HISTORY_FOR_SIGNAL
        sim_mod.MIN_HISTORY_FOR_SIGNAL = 0
        try:
            idx, sims = find_similar(query, hist, k=10, current_ts=current_ts)
            assert len(idx) == 3  # capped by usable
        finally:
            sim_mod.MIN_HISTORY_FOR_SIGNAL = original
