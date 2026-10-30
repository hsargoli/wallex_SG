"""Analyzer-only backtest — pure functions + main loop.

Design:
    - split_train_test: time-based split (NOT random) for leakage safety.
    - simulate_trade: single-trade PnL from SL/TP/time-exit. No trailing.
    - run_backtest: wires features + similarity + outcome. Requires I/O,
      so it's not unit-tested here — validated by smoke/full run output.

HONEST scope:
    This backtest tests ANALYZER ONLY — no BB Squeeze, no gate, no
    trailing. Its PF will be lower than the full sarv_tiger strategy.
    Purpose: does the analyzer's "pattern memory" have standalone edge?
"""
from __future__ import annotations

import numpy as np
from dataclasses import dataclass
from typing import Any

from app.domain.entities.candle import Candle
from app.services.bots.sarv_tiger.analyzer.analyzer_config import AnalyzerConfig
from app.services.bots.sarv_tiger.analyzer.features import extract_features
from app.services.bots.sarv_tiger.analyzer.history import HORIZON_168H
from app.services.bots.sarv_tiger.analyzer.outcome import (
    analyze_outcomes,
    compute_baseline,
)
from app.services.bots.sarv_tiger.analyzer.similarity import find_similar

ATR_PERIOD = 14
SL_ATR_MULT = 1.2
import os as _os
TP_ATR_MULT = float(_os.environ.get('TP_ATR_MULT', '8.0'))


@dataclass(slots=True)
class TradeResult:
    entry_ts: int
    exit_ts: int
    entry_price: float
    exit_price: float
    pnl_pct: float
    reason: str  # "tp" | "sl" | "time"


@dataclass(slots=True)
class BacktestResult:
    trades: list[TradeResult]
    pf: float
    win_rate: float
    total_pnl: float
    max_dd: float
    avg_ret: float


def split_train_test(
    items: list[Any], train_ratio: float = 0.7,
) -> tuple[list[Any], list[Any]]:
    """Time-based split. Order preserved. Leakage-safe by construction."""
    if not (0.0 < train_ratio < 1.0):
        raise ValueError(f"train_ratio must be in (0, 1), got {train_ratio}")
    n = len(items)
    cut = int(n * train_ratio)
    return items[:cut], items[cut:]


def simulate_trade(
    entry: float, sl: float, tp: float, future: list[Candle],
) -> tuple[float | None, str]:
    """Simulate one trade. Returns (pnl_pct, reason).

    Rules:
      - Within a candle: SL priority (conservative).
      - Across candles: chronological — first hit wins.
      - No hit → time exit at last close.
      - Empty future → (None, "no_future").

    pnl_pct = (exit - entry) / entry  (fraction, not %).
    """
    if not future:
        return None, "no_future"

    for c in future:
        low = float(c.low)
        high = float(c.high)
        if low <= sl:
            return (sl - entry) / entry, "sl"
        if high >= tp:
            return (tp - entry) / entry, "tp"

    last_close = float(future[-1].close)
    return (last_close - entry) / entry, "time"


def _atr_at(
    candles: list[Candle], end_idx: int, period: int = ATR_PERIOD,
) -> float:
    if end_idx < period:
        return 0.0
    trs = []
    for i in range(end_idx - period + 1, end_idx + 1):
        h = float(candles[i].high)
        l = float(candles[i].low)
        prev_c = float(candles[i - 1].close)
        trs.append(max(h - l, abs(h - prev_c), abs(l - prev_c)))
    return sum(trs) / period


def _compute_metrics(trades: list[TradeResult]) -> tuple[float, float, float, float, float]:
    """Return (pf, win_rate, total_pnl, max_dd, avg_ret)."""
    if not trades:
        return 0.0, 0.0, 0.0, 0.0, 0.0

    wins = [t.pnl_pct for t in trades if t.pnl_pct > 0]
    losses = [t.pnl_pct for t in trades if t.pnl_pct <= 0]

    gross_win = sum(wins)
    gross_loss = abs(sum(losses))
    pf = gross_win / gross_loss if gross_loss > 0 else float("inf")
    win_rate = len(wins) / len(trades)
    total_pnl = sum(t.pnl_pct for t in trades)

    # Max drawdown on cumulative PnL
    cum = np.cumsum([t.pnl_pct for t in trades])
    peak = np.maximum.accumulate(cum)
    dd = peak - cum
    max_dd = float(np.max(dd)) if len(dd) else 0.0

    avg_ret = total_pnl / len(trades)
    return pf, win_rate, total_pnl, max_dd, avg_ret


def run_backtest(
    windows: list[dict[str, Any]],
    candles_4h: list[Candle],
    cfg: AnalyzerConfig | None = None,
    train_ratio: float = 0.7,
    k: int = 50,
    verbose: bool = False,
) -> tuple[BacktestResult, BacktestResult]:
    """Run analyzer-only backtest. Returns (train_result, test_result).

    Assumes `windows` are in chronological order, and each window's
    `window_end_ts` maps to an index in `candles_4h`.
    """
    cfg = cfg or AnalyzerConfig()
    n = len(windows)
    if n < 100:
        empty = BacktestResult([], 0.0, 0.0, 0.0, 0.0, 0.0)
        return empty, empty

    train_windows, test_windows = split_train_test(windows, train_ratio)

    # --- Compute train stats (leakage-safe normalization) ---
    train_feats = np.array(
        [w["features"] for w in train_windows], dtype=float,
    )
    train_mean = np.mean(train_feats, axis=0)
    train_std = np.std(train_feats, axis=0)
    train_std = np.where(train_std < 1e-9, 1.0, train_std)

    # Baseline: computed from TRAIN only (test is held out)
    baseline = compute_baseline(train_windows)

    # ts -> index map for candles_4h
    ts_to_idx = {int(c.time): i for i, c in enumerate(candles_4h)}

    def _run_on(split_windows: list[dict], history_pool: list[dict]) -> list[TradeResult]:
        out: list[TradeResult] = []
        for w in split_windows:
            end_ts = int(w["window_end_ts"])
            end_idx = ts_to_idx.get(end_ts)
            if end_idx is None:
                continue

            # Build query: last 20 candles ending at end_idx, normalized
            if end_idx < 20:
                continue
            query_raw = extract_features(
                candles_4h[end_idx - 19 : end_idx + 1], window=20,
            )
            if query_raw is None:
                continue
            query = (query_raw - train_mean) / train_std
            query = np.clip(query, -3.0, 3.0)

            # Similarity (leakage-safe inside)
            idx, _ = find_similar(
                query, history_pool, k=k, current_ts=end_ts + 4 * 3600,
            )
            if len(idx) == 0:
                continue

            top_k = [history_pool[i] for i in idx]
            analysis = analyze_outcomes(top_k, cfg, baseline)
            if analysis.signal != "long":
                continue

            entry = float(candles_4h[end_idx].close)
            atr = _atr_at(candles_4h, end_idx)
            if atr <= 0:
                continue
            sl = entry - SL_ATR_MULT * atr
            tp = entry + TP_ATR_MULT * atr
            future = candles_4h[end_idx + 1 : end_idx + 1 + HORIZON_168H]
            pnl, reason = simulate_trade(entry, sl, tp, future)
            if pnl is None:
                continue
            exit_ts = int(future[-1].time) if reason == "time" else end_ts
            out.append(TradeResult(
                entry_ts=end_ts,
                exit_ts=exit_ts,
                entry_price=entry,
                exit_price=entry * (1 + pnl),
                pnl_pct=pnl,
                reason=reason,
            ))
        return out

    # Train: each window can only use earlier train windows as history
    # (leakage-safe). We iterate in order and grow the pool.
    train_trades: list[TradeResult] = []
    for i, w in enumerate(train_windows):
        if i < 100:
            continue
        pool = train_windows[:i]
        train_trades.extend(_run_on([w], pool))

    # Test: history = ALL train windows (which are all before test period).
    test_trades = _run_on(test_windows, train_windows)

    train_pf, train_wr, train_pnl, train_dd, train_avg = _compute_metrics(train_trades)
    test_pf, test_wr, test_pnl, test_dd, test_avg = _compute_metrics(test_trades)

    train_res = BacktestResult(
        trades=train_trades, pf=train_pf, win_rate=train_wr,
        total_pnl=train_pnl, max_dd=train_dd, avg_ret=train_avg,
    )
    test_res = BacktestResult(
        trades=test_trades, pf=test_pf, win_rate=test_wr,
        total_pnl=test_pnl, max_dd=test_dd, avg_ret=test_avg,
    )

    if verbose:
        print(f"train: {len(train_trades)} trades, PF={train_pf:.2f}, WR={train_wr:.1%}")
        print(f"test:  {len(test_trades)} trades, PF={test_pf:.2f}, WR={test_wr:.1%}")

    return train_res, test_res
