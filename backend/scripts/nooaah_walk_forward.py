"""Walk-forward validation for Nooaah.

روش:
  - کل داده رو به N پنجره‌ی مساوی تقسیم کن
  - هر پنجره یه backtest مستقل (با warmup context از قبل)
  - گزارش: چند پنجره مثبت، میانگین، واریانس

Usage (from ~/wallex/backend):
    uv run python -m scripts.nooaah_walk_forward --limit 700 --windows 5
"""

from __future__ import annotations

import argparse
import asyncio
import statistics
from dataclasses import dataclass

from app.application.use_cases.get_candles import GetCandlesUseCase
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.domain.entities.candle import Candle
from app.infrastructure.exchange.wallex.client import WallexExchange
from app.services.bots.nooaah.backtest import run_nooaah_backtest
from app.services.bots.nooaah.bot import NooaahBot
from app.services.bots.nooaah.config import NooaahConfig


@dataclass(slots=True)
class WindowResult:
    idx: int
    start: int
    end: int
    trades: int
    win_rate: float
    total_return: float
    max_dd: float
    profit_factor: float
    sharpe: float
    error: str | None = None


def build_windows(
    total: int, warmup: int, n_windows: int
) -> list[tuple[int, int]]:
    """پنجره‌های مساوی از warmup تا total."""
    if total <= warmup + 50 * n_windows:
        raise ValueError(
            f"data too short: total={total}, warmup={warmup}, "
            f"windows={n_windows}, need ≥ {warmup + 50 * n_windows}"
        )
    window_size = (total - warmup) // n_windows
    windows = []
    for k in range(n_windows):
        start = warmup + k * window_size
        end = warmup + (k + 1) * window_size if k < n_windows - 1 else total
        windows.append((start, end))
    return windows


async def fetch(symbols: list[str], limit: int) -> dict[str, list[Candle]]:
    settings = get_settings()
    ex = WallexExchange.create(settings)
    try:
        uc = GetCandlesUseCase(exchange=ex)
        data: dict[str, list[Candle]] = {}
        for sym in symbols:
            try:
                c = await uc.execute(symbol=sym, timeframe="1h", limit=limit)
                if c:
                    data[sym] = c
                    print(f"  ✅ {sym}: {len(c)}")
            except Exception as e:
                print(f"  ❌ {sym}: {e}")
        return data
    finally:
        await ex.aclose()


def print_report(windows: list[WindowResult], cfg: NooaahConfig) -> None:
    print(f"\n{'=' * 110}")
    print(f"  📊 Walk-Forward Report — N={len(windows)} windows")
    print(f"  config: top_n={cfg.top_n}  conf={cfg.min_confidence}  "
          f"tp={cfg.tp_atr_mult}  sl={cfg.sl_atr_mult}")
    print(f"{'=' * 110}")
    print(
        f"  {'#':>3} {'range':>12} {'trades':>7} {'WR%':>6} "
        f"{'ret%':>8} {'DD%':>6} {'PF':>6} {'Sharpe':>8}"
    )
    print("-" * 110)
    for w in windows:
        if w.error:
            print(f"  {w.idx:>3} [{w.start:>4}:{w.end:<4}] ❌ {w.error}")
            continue
        print(
            f"  {w.idx:>3} [{w.start:>4}:{w.end:<4}] {w.trades:>7} "
            f"{w.win_rate:>6.1f} {w.total_return:>+8.2f} {w.max_dd:>6.2f} "
            f"{w.profit_factor:>6.2f} {w.sharpe:>8.3f}"
        )

    valid = [w for w in windows if w.error is None]
    if not valid:
        print("\n  ❌ no valid windows")
        return

    positive = [w for w in valid if w.total_return > 0]
    negative = [w for w in valid if w.total_return < 0]
    zero = [w for w in valid if w.total_return == 0]

    avg_ret = statistics.mean(w.total_return for w in valid)
    med_ret = statistics.median(w.total_return for w in valid)
    std_ret = statistics.stdev(w.total_return for w in valid) if len(valid) > 1 else 0.0
    total_trades = sum(w.trades for w in valid)

    print(f"\n{'=' * 110}")
    print(f"  🎯 Summary")
    print(f"{'=' * 110}")
    print(f"  windows:              {len(valid)}")
    print(f"  positive / negative:  {len(positive)} / {len(negative)}")
    print(f"  zero trades:          {len(zero)}")
    print(f"  avg return:           {avg_ret:+.2f}%")
    print(f"  median return:        {med_ret:+.2f}%")
    print(f"  std of returns:       {std_ret:.2f}%")
    print(f"  total trades:         {total_trades}")

    pct_positive = len(positive) / len(valid) * 100 if valid else 0
    print(f"  consistency:          {pct_positive:.0f}% windows positive")

    print()
    if pct_positive >= 60 and avg_ret > 0:
        print("  ✅ ROBUST — استراتژی در اکثر پنجره‌ها مثبت بوده")
    elif pct_positive >= 40:
        print("  🟡 MIXED — بستگی به رژیم بازار داره")
    else:
        print("  ❌ FRAGILE — استراتژی به یه دوره‌ی خاص وابسته‌ست")


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=700)
    parser.add_argument("--max-symbols", type=int, default=5)
    parser.add_argument("--windows", type=int, default=5)
    parser.add_argument("--warmup", type=int, default=120)
    parser.add_argument("--conf", type=int, default=60)
    parser.add_argument("--tp", type=float, default=3.0)
    parser.add_argument("--sl", type=float, default=1.5)
    args = parser.parse_args()

    configure_logging()
    settings = get_settings()
    ex = WallexExchange.create(settings)

    try:
        bot = NooaahBot(exchange=ex, config=NooaahConfig())
        symbols = await bot.pick_top_symbols(args.max_symbols)
    finally:
        await ex.aclose()

    print(f"📥 Top {len(symbols)}: {symbols}\n")
    print(f"📥 Fetching {args.limit} candles per symbol...")
    data = await fetch(symbols, args.limit)
    if not data:
        print("❌ no data")
        return

    actual = min(len(c) for c in data.values())
    cfg = NooaahConfig(
        top_n=args.max_symbols,
        min_confidence=args.conf,
        tp_atr_mult=args.tp,
        sl_atr_mult=args.sl,
    )

    windows = build_windows(actual, args.warmup, args.windows)
    print(f"\n📊 {len(windows)} windows of ~{windows[0][1] - windows[0][0]} candles")
    print(f"   total={actual}, warmup={args.warmup}\n")

    results: list[WindowResult] = []
    for idx, (start, end) in enumerate(windows, 1):
        try:
            stats = run_nooaah_backtest(
                data, cfg, warmup=args.warmup, start_idx=start, end_idx=end
            )
            results.append(WindowResult(
                idx=idx, start=start, end=end,
                trades=stats.total_trades,
                win_rate=stats.win_rate,
                total_return=stats.total_return_pct,
                max_dd=stats.max_drawdown_pct,
                profit_factor=stats.profit_factor,
                sharpe=stats.sharpe_ratio,
            ))
        except ValueError as e:
            results.append(WindowResult(
                idx=idx, start=start, end=end,
                trades=0, win_rate=0, total_return=0, max_dd=0,
                profit_factor=0, sharpe=0, error=str(e),
            ))

    print_report(results, cfg)


if __name__ == "__main__":
    asyncio.run(main())
