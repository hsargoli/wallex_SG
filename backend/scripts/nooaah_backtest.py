"""Nooaah backtest — CLI (reuses services/backtest.py Trade/BacktestResult).

Usage (from ~/wallex/backend):
    uv run python -m scripts.nooaah_backtest --top 5 --limit 500
"""

from __future__ import annotations

import argparse
import asyncio

from app.application.use_cases.get_candles import GetCandlesUseCase
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.infrastructure.exchange.wallex.client import WallexExchange
from app.services.bots.nooaah.backtest import run_nooaah_backtest
from app.services.bots.nooaah.bot import NooaahBot
from app.services.bots.nooaah.config import NooaahConfig


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--top", type=int, default=5)
    parser.add_argument("--limit", type=int, default=500)
    parser.add_argument("--min-confidence", type=int, default=None)
    args = parser.parse_args()

    configure_logging()
    settings = get_settings()
    exchange = WallexExchange.create(settings)

    try:
        cfg_kwargs = {"top_n": args.top}
        if args.min_confidence is not None:
            cfg_kwargs["min_confidence"] = args.min_confidence
        cfg = NooaahConfig(**cfg_kwargs)

        bot = NooaahBot(exchange=exchange, config=cfg)
        symbols = await bot.pick_top_symbols(args.top)
        print(f"📥 Fetching {args.limit} candles for {len(symbols)} symbols...")

        uc = GetCandlesUseCase(exchange=exchange)
        candles_by_symbol = {}
        for sym in symbols:
            try:
                c = await uc.execute(
                    symbol=sym, timeframe="1h", limit=args.limit
                )
                if c:
                    candles_by_symbol[sym] = c
                    print(f"  ✅ {sym}: {len(c)} candles")
            except Exception as e:
                print(f"  ❌ {sym}: {e}")

        if not candles_by_symbol:
            print("❌ no data")
            return

        print("\n🧪 Running Nooaah backtest...")
        stats = run_nooaah_backtest(candles_by_symbol, cfg)

        print()
        print("=" * 70)
        print("  📊 Nooaah Backtest (multi-symbol)")
        print("=" * 70)
        print(f"  symbols:            {list(candles_by_symbol.keys())}")
        print(f"  candles_scanned:    {stats.candles_analyzed}")
        print(f"  signals_computed:   {stats.signals_generated}")
        print(f"  trades executed:    {stats.total_trades}")
        print(f"  wins / losses:      {stats.wins} / {stats.losses}")
        print(f"  win rate:           {stats.win_rate:.1f}%")
        print(f"  total return:       {stats.total_return_pct:+.2f}%")
        print(f"  max drawdown:       {stats.max_drawdown_pct:.2f}%")
        print(f"  profit factor:      {stats.profit_factor:.2f}")
        print(f"  sharpe:             {stats.sharpe_ratio:.2f}")
        print(f"  avg duration:       {stats.avg_duration_candles:.1f}h")
        print("=" * 70)
        if stats.trades:
            print("\n  last 5 trades:")
            for t in stats.trades[-5:]:
                print(
                    f"    {t.side:4} {t.entry_price:>14} → "
                    f"{t.exit_price:>14}  {t.exit_reason:10}  "
                    f"{t.return_pct:+6.2f}%  conf={t.confidence}  "
                    f"dur={t.duration_candles}h"
                )
    finally:
        await exchange.aclose()


if __name__ == "__main__":
    asyncio.run(main())
