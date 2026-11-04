"""Backtest SarvRouter + Nooaah on BTCUSDT (5 years) — proxy verdict.

⚠️ BTCUSDT (Binance) ≠ BTCMN (Wallex) — price differs.
But strategy mechanics (RSI, ATR, regime) are symbol-independent.
This is a PROXY verdict, not final.

Success criteria (AP-57):
- SarvRouter: 10-50 switches over 5yr, 0 kill_events, cash_trace sane
- Nooaah: 30+ trades, WR > 45%, PF > 1.0
"""
from __future__ import annotations

import sys
import tempfile
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, "backend")

import pandas as pd
from app.domain.entities.candle import Candle
from app.services.bots.sarv_router.bot import SarvRouter
from app.services.bots.sarv_router.config import SarvRouterConfig
from app.services.bots.sarv_router.store import SarvStore
from app.services.bots.sarv_router.audit import AuditTrail
from app.services.bots.sarv_router.backtest_adapter import run_sarv_backtest
from app.services.bots.nooaah.backtest import run_nooaah_backtest
from app.services.bots.nooaah.config import NooaahConfig


DATA = Path("research/tsfresh/data/BTCUSDT_1h_full.csv")


def load_candles(csv_path: Path) -> list[Candle]:
    df = pd.read_csv(csv_path)
    # pandas 2.x returns microseconds for .astype("int64") on datetime
    # Use per-row .timestamp() to be version-independent
    times = df["datetime"].apply(lambda x: int(pd.Timestamp(x).timestamp())).values
    candles = []
    for i, row in df.iterrows():
        candles.append(Candle(
            time=int(times[i]),
            open=Decimal(str(row["open"])),
            high=Decimal(str(row["high"])),
            low=Decimal(str(row["low"])),
            close=Decimal(str(row["close"])),
            volume=Decimal(str(row["volume"])),
        ))
    return candles


def main() -> None:
    import sys
    import time

    limit = None
    for i, a in enumerate(sys.argv):
        if a == "--limit" and i + 1 < len(sys.argv):
            limit = int(sys.argv[i + 1])

    print("=" * 60)
    print(f"  Backtest BTCUSDT (proxy) — limit={limit or 'full'}")
    print("=" * 60)

    print(f"\n[1] Loading {DATA}")
    candles = load_candles(DATA)
    if limit:
        candles = candles[:limit]
    print(f"    {len(candles)} candles")
    print(f"    first: {pd.Timestamp(candles[0].time, unit='s')}")
    print(f"    last:  {pd.Timestamp(candles[-1].time, unit='s')}")

    # ─── SarvRouter ───
    print(f"\n[2] SarvRouter (single symbol)")
    tmp = Path(tempfile.mkdtemp())
    t_sarv_start = time.time()
    router = SarvRouter(
        config=SarvRouterConfig(),
        start_bot=lambda s: None,
        stop_bot=lambda s: None,
        stop_all=lambda: None,
        store=SarvStore(base_dir=tmp),
        audit=AuditTrail(base_dir=tmp),
    )
    # monkey-patch store.save for progress
    _orig_save = router.store.save
    _tick_counter = [0]
    def _patched_save(*args, **kwargs):
        _tick_counter[0] += 1
        if _tick_counter[0] % 5000 == 0:
            print(f"    [progress] {_tick_counter[0]} ticks in {time.time()-t_sarv_start:.0f}s", flush=True)
        return _orig_save(*args, **kwargs)
    router.store.save = _patched_save

    sarv = run_sarv_backtest(router, "btc-proxy", candles)
    print(f"    [done] {_tick_counter[0]} ticks in {time.time()-t_sarv_start:.1f}s", flush=True)
    print(f"    total_ticks: {sarv['total_ticks']}")
    print(f"    switches: {sarv['switches']}")
    print(f"    kill_events: {sarv['kill_events']}")
    print(f"    final_regime: {sarv['final_regime']}")
    print(f"    final_active_bots: {sarv['final_active_bots']}")
    cash = sarv["cash_trace"]
    print(f"    cash: {cash[0]:.0f} → {cash[-1]:.0f}")
    print(f"    cash min/max: {min(cash):.0f} / {max(cash):.0f}")
    # regime sequence stats
    seq = sarv["regime_sequence"]
    from collections import Counter
    regime_counts = Counter(seq)
    print(f"    regime distribution: {dict(regime_counts)}")

    # ─── Nooaah (single symbol BTCUSDT as proxy) ───
    print(f"\n[3] Nooaah (BTCUSDT only — proxy, not 5 symbols)")
    try:
        nooaah = run_nooaah_backtest(
            candles_by_symbol={"BTCUSDT": candles},
            config=NooaahConfig(),
            start_idx=200,
        )
        print(f"    candles_analyzed: {nooaah.candles_analyzed}")
        print(f"    total_trades: {len(nooaah.trades)}")
        if nooaah.trades:
            rets = [t.return_pct for t in nooaah.trades]
            wins = sum(1 for r in rets if r > 0)
            losses = len(rets) - wins
            wr = wins / len(rets)
            gross_win = sum(r for r in rets if r > 0)
            gross_loss = abs(sum(r for r in rets if r <= 0))
            pf = gross_win / gross_loss if gross_loss > 0 else float("inf")
            print(f"    wins: {wins} | losses: {losses} | WR: {wr:.1%}")
            print(f"    avg return_pct: {sum(rets)/len(rets):.2f}%")
            print(f"    PF (gross): {pf:.2f}")
            print(f"    best/worst: {max(rets):.2f}% / {min(rets):.2f}%")
            print(f"    exit reasons: ", end="")
            from collections import Counter
            print(dict(Counter(t.exit_reason for t in nooaah.trades)))
    except Exception as e:
        print(f"    ❌ {type(e).__name__}: {e}")

    # ─── Verdict (per AP-57) ───
    print(f"\n{'=' * 60}")
    print("  VERDICT (AP-57 criteria)")
    print(f"{'=' * 60}")
    sarv_switches = sarv["switches"]
    sarv_kills = sarv["kill_events"]
    sarv_ok = (10 <= sarv_switches <= 50) and sarv_kills == 0
    print(f"  SarvRouter: switches={sarv_switches} (10-50?), kills={sarv_kills} (0?) → {'✅ PASS' if sarv_ok else '❌ FAIL'}")

    print(f"\n⚠️ NOTE: BTCUSDT is a PROXY for BTCMN. Verify on Wallex data before Live.")


if __name__ == "__main__":
    main()
