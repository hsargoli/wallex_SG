"""Walk-forward parameter tuning for scalp_master.

Splits data into overlapping train/test folds, searches a small grid
on each train window, picks the best (by PF, tiebreak win-rate) and
evaluates it on the test window. No look-ahead.
"""
from __future__ import annotations
import argparse, csv, itertools, sys
from dataclasses import replace
from decimal import Decimal
from pathlib import Path

_BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

from app.domain.entities.candle import Candle
from app.services.bots.scalp_master.config import ScalpMasterConfig


def split_walk_forward(start_ts: int, end_ts: int,
                       train_size: int, test_size: int) -> list[dict]:
    """Return overlapping (train, test) folds. Strictly increasing test starts."""
    if train_size <= 0 or test_size <= 0:
        raise ValueError("train_size/test_size must be positive")
    folds = []
    cursor = start_ts
    while cursor + train_size + test_size <= end_ts:
        folds.append({
            "train": (cursor, cursor + train_size),
            "test":  (cursor + train_size, cursor + train_size + test_size),
        })
        cursor += test_size
    return folds


def default_grid() -> dict[str, list]:
    """Small sensible grid (<= 3 * 3 * 2 * 2 * 2 * 3 = 216 combos)."""
    return {
        "drop_threshold_pct": [2.0, 2.5, 3.5],
        "rsi_min": [20.0, 25.0, 30.0],
        "rsi_max": [45.0, 50.0],
        "sl_atr_mult": [1.2, 1.5],
        "tp_atr_mult": [2.5, 3.0],
        "trend_ema_gap_pct": [3.0, 5.0, 7.0],
    }


def apply_params(base: ScalpMasterConfig, params: dict) -> ScalpMasterConfig:
    return replace(base, **params)


def load_candles_csv(path: Path) -> list[Candle]:
    out: list[Candle] = []
    with path.open("r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            ts = int(row["open_time"])
            if ts > 10_000_000_000:  # ms → s normalization
                ts //= 1000
            out.append(Candle(
                time=ts,
                open=Decimal(str(row["open"])),
                high=Decimal(str(row["high"])),
                low=Decimal(str(row["low"])),
                close=Decimal(str(row["close"])),
                volume=Decimal(str(row["volume"])),
            ))
    return out


def _filter(candles: list[Candle], a: int, b: int) -> list[Candle]:
    return [c for c in candles if a <= c.time < b]


def run_one(candles: list[Candle], cfg: ScalpMasterConfig,
            capital: float, fee_pct: float,
            slippage_pct: float, spread_pct: float) -> dict:
    from app.infrastructure.backtest.bot_backtest import run_scalp_backtest
    if len(candles) < cfg.warmup_candles + 10:
        return {"total_trades": 0, "total_pnl_pct": 0.0,
                "profit_factor": None, "win_rate": 0.0,
                "max_drawdown_pct": 0.0}
    return run_scalp_backtest(
        candles, initial_capital=capital, position_size_pct=50.0,
        fee_pct=fee_pct, slippage_pct=slippage_pct, spread_pct=spread_pct,
        config=cfg,
    )


def _score(r: dict) -> tuple[float, float]:
    """Higher is better: PF first, then win-rate."""
    pf = r.get("profit_factor")
    pf_val = pf if isinstance(pf, (int, float)) else 0.0
    return (float(pf_val), float(r.get("win_rate", 0.0)))
