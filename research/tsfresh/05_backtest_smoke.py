"""Smoke test: run SarvRouter + Nooaah backtest on existing data.

Purpose: verify mechanics work (no verdict — data too short).
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, "backend")

from decimal import Decimal
from app.domain.entities.candle import Candle
from app.services.bots.sarv_router.bot import SarvRouter
from app.services.bots.sarv_router.config import SarvRouterConfig
from app.services.bots.sarv_router.store import SarvStore
from app.services.bots.sarv_router.audit import AuditTrail
from app.services.bots.sarv_router.backtest_adapter import run_sarv_backtest
from app.services.bots.nooaah.backtest import run_nooaah_backtest
from app.services.bots.nooaah.config import NooaahConfig


def load_candles_1h(csv_path: Path) -> list[Candle]:
    """Load 1h candles from CSV. Handles both `datetime` and `open_time` columns.

    - `datetime`: ISO string (research/tsfresh BTCUSDT_1h_full.csv)
    - `open_time`: Unix seconds or ms (backend/data/candles/BTCTMN_1h.csv)
    """
    import pandas as pd

    df = pd.read_csv(csv_path)
    if "datetime" in df.columns:
        times = pd.to_datetime(df["datetime"]).astype("int64") // 10**9
    elif "open_time" in df.columns:
        vals = df["open_time"].astype("int64")
        # detect seconds vs ms vs us (AP-62)
        sample = int(vals.iloc[0])
        if sample > 10**15:
            times = vals // 10**6        # us → s
        elif sample > 10**12:
            times = vals // 10**3        # ms → s
        else:
            times = vals                 # already s
    else:
        raise ValueError(f"No datetime/open_time column in {csv_path}")

    candles = []
    for i, row in df.iterrows():
        candles.append(Candle(
            time=int(times.iloc[i]),
            open=Decimal(str(row["open"])),
            high=Decimal(str(row["high"])),
            low=Decimal(str(row["low"])),
            close=Decimal(str(row["close"])),
            volume=Decimal(str(row["volume"])),
        ))
    return candles


def main() -> None:
    print("=" * 60)
    print("  Smoke test: SarvRouter + Nooaah backtest")
    print("=" * 60)

    # ─── Load data ───
    btc_tmn = load_candles_1h(Path("backend/data/candles/BTCTMN_1h.csv"))
    eth_tmn = load_candles_1h(Path("backend/data/candles/ETHTMN_1h.csv"))
    usdt_tmn = load_candles_1h(Path("backend/data/candles/USDTTMN_1h.csv"))
    print(f"\n[1] Loaded:")
    print(f"    BTCTMN: {len(btc_tmn)} candles")
    print(f"    ETHTMN: {len(eth_tmn)} candles")
    print(f"    USDTTMN: {len(usdt_tmn)} candles")

    # ─── SarvRouter backtest (single symbol) ───
    print(f"\n[2] SarvRouter backtest (BTCTMN, {len(btc_tmn)} ticks)")
    import tempfile
    tmp = Path(tempfile.mkdtemp())
    router = SarvRouter(
        config=SarvRouterConfig(),
        start_bot=lambda s: None,
        stop_bot=lambda s: None,
        stop_all=lambda: None,
        store=SarvStore(base_dir=tmp),
        audit=AuditTrail(base_dir=tmp),
    )
    sarv_result = run_sarv_backtest(router, "smoke", btc_tmn)
    print(f"    total_ticks: {sarv_result['total_ticks']}")
    print(f"    switches: {sarv_result['switches']}")
    print(f"    kill_events: {sarv_result['kill_events']}")
    print(f"    final_regime: {sarv_result['final_regime']}")
    print(f"    final_active_bots: {sarv_result['final_active_bots']}")
    print(f"    final_cash: {sarv_result['final_cash']}")
    print(f"    cash_trace (first/last): {sarv_result['cash_trace'][0]} → {sarv_result['cash_trace'][-1]}")

    # ─── Nooaah backtest (multi-symbol) ───
    print(f"\n[3] Nooaah backtest (3 symbols, ~{min(len(btc_tmn), len(eth_tmn), len(usdt_tmn))} ticks)")
    try:
        nooaah_result = run_nooaah_backtest(
            candles_by_symbol={
                "BTCTMN": btc_tmn,
                "ETHTMN": eth_tmn,
                "USDTTMN": usdt_tmn,
            },
            config=NooaahConfig(),
            start_idx=200,  # warmup
        )
        print(f"    symbol: {nooaah_result.symbol}")
        print(f"    candles_analyzed: {nooaah_result.candles_analyzed}")
        print(f"    total_trades: {len(nooaah_result.trades)}")
        if nooaah_result.trades:
            # Trade attributes vary — use getattr with fallback
            first = nooaah_result.trades[0]
            trade_attrs = [a for a in dir(first) if not a.startswith("_")]
            print(f"    Trade attrs: {trade_attrs}")
            # Try common names
            pnl_attr = next(
                (a for a in ("pnl", "pnl_pct", "profit", "net_pnl", "return_pct")
                 if hasattr(first, a)),
                None
            )
            if pnl_attr:
                wins = sum(1 for t in nooaah_result.trades if getattr(t, pnl_attr) > 0)
                losses = len(nooaah_result.trades) - wins
                print(f"    wins: {wins} | losses: {losses} (using {pnl_attr})")
            else:
                print("    ⚠️ no PnL-like attribute found — inspect Trade class")
    except Exception as e:
        print(f"    ❌ Nooaah backtest failed: {type(e).__name__}: {e}")

    print(f"\n{'=' * 60}")
    print("  ✅ Smoke test complete (mechanics verified)")
    print(f"{'=' * 60}")
    print("\n⚠️ NOTE: Data is only ~56 days — this is a MECHANICS test, not a verdict.")
    print("   For statistical verdict: use BTCUSDT 5yr proxy or fetch more Wallex data.")


if __name__ == "__main__":
    main()
