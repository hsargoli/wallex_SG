"""Nooaah per-symbol analysis — کدوم نماد برنده، کدوم بازنده.

برای هر نماد جداگانه یه backtest مستقل اجرا می‌کنه.

Usage (from ~/wallex/backend):
    uv run python -m scripts.nooaah_per_symbol --start 2026-09-25 --end 2026-10-05
"""

from __future__ import annotations

import argparse
import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone

from app.application.use_cases.get_candles import GetCandlesUseCase
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.domain.entities.candle import Candle
from app.infrastructure.exchange.wallex.client import WallexExchange
from app.services.bots.nooaah.backtest import run_nooaah_backtest
from app.services.bots.nooaah.bot import NooaahBot
from app.services.bots.nooaah.config import NooaahConfig


@dataclass(slots=True)
class SymbolResult:
    symbol: str
    trades: int
    wins: int
    losses: int
    win_rate: float
    total_return: float
    max_dd: float
    profit_factor: float
    sharpe: float
    avg_duration: float
    buy_hold: float
    error: str | None = None


def parse_date(s: str) -> int:
    dt = datetime.strptime(s, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    return int(dt.timestamp())


def find_idx_range(
    candles: list[Candle], start_ts: int, end_ts: int
) -> tuple[int, int]:
    start_idx = None
    end_idx = len(candles)
    for i, c in enumerate(candles):
        if start_idx is None and c.time >= start_ts:
            start_idx = i
        if c.time >= end_ts:
            end_idx = i
            break
    if start_idx is None:
        raise ValueError("no candles in range")
    return start_idx, end_idx


async def fetch_one(
    uc: GetCandlesUseCase, symbol: str, limit: int
) -> list[Candle]:
    try:
        return await uc.execute(symbol=symbol, timeframe="1h", limit=limit)
    except Exception:
        return []


def verdict(r: SymbolResult) -> str:
    """ارزیابی نماد."""
    if r.error:
        return "❌ خطا"
    if r.trades == 0:
        return "⚪ بی‌معامله"
    if r.trades < 3:
        return "🟡 نمونه کم"
    if r.total_return > 5 and r.win_rate >= 60:
        return "✅ ستاره"
    if r.total_return > 0 and r.win_rate >= 50:
        return "✅ خوب"
    if r.total_return > -2:
        return "🟡 متوسط"
    return "❌ ضعیف"


def print_report(
    results: list[SymbolResult], start: str, end: str, cfg: NooaahConfig
) -> None:
    print()
    print("=" * 115)
    print(f"  📊 Per-Symbol Performance — {start} → {end}")
    print(
        f"  config: conf={cfg.min_confidence}  tp={cfg.tp_atr_mult}  "
        f"sl={cfg.sl_atr_mult}  cc={cfg.confirmation_candles}"
    )
    print("=" * 115)
    print(
        f"  {'نماد':<12} {'trades':>7} {'WR%':>7} {'ret%':>9} "
        f"{'DD%':>7} {'PF':>6} {'Sharpe':>8} {'مدت':>6} {'B&H':>8}  verdict"
    )
    print("-" * 115)
    for r in sorted(results, key=lambda x: x.total_return, reverse=True):
        if r.error:
            print(f"  {r.symbol:<12} ❌ {r.error}")
            continue
        print(
            f"  {r.symbol:<12} {r.trades:>7} {r.win_rate:>7.1f} "
            f"{r.total_return:>+9.2f} {r.max_dd:>7.2f} "
            f"{r.profit_factor:>6.2f} {r.sharpe:>8.3f} "
            f"{r.avg_duration:>5.1f}h {r.buy_hold:>+7.2f}%  {verdict(r)}"
        )

    # خلاصه
    valid = [r for r in results if r.error is None]
    if not valid:
        return
    winners = [r for r in valid if r.total_return > 2 and r.win_rate >= 55]
    losers = [r for r in valid if r.total_return < -2]
    middles = [
        r for r in valid
        if r not in winners and r not in losers and r.trades > 0
    ]
    silent = [r for r in valid if r.trades == 0]

    print()
    print("=" * 115)
    print("  🎯 خلاصه")
    print("=" * 115)
    if winners:
        print(f"  ✅ برنده‌ها ({len(winners)}):  " + ", ".join(r.symbol for r in winners))
    if middles:
        print(f"  🟡 متوسط ({len(middles)}):    " + ", ".join(r.symbol for r in middles))
    if losers:
        print(f"  ❌ بازنده‌ها ({len(losers)}):  " + ", ".join(r.symbol for r in losers))
    if silent:
        print(f"  ⚪ بی‌معامله ({len(silent)}):  " + ", ".join(r.symbol for r in silent))

    # پیشنهاد
    print()
    if winners:
        print(f"  💡 whitelist پیشنهادی: " + ", ".join(r.symbol for r in winners))


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", required=True, help="YYYY-MM-DD")
    parser.add_argument("--end", required=True, help="YYYY-MM-DD")
    parser.add_argument("--symbols", default=None, help="comma-separated")
    parser.add_argument("--top", type=int, default=5)
    parser.add_argument("--limit", type=int, default=700)
    parser.add_argument("--conf", type=int, default=85)
    parser.add_argument("--tp", type=float, default=3.0)
    parser.add_argument("--sl", type=float, default=1.5)
    parser.add_argument("--cc", type=int, default=2)
    parser.add_argument("--warmup", type=int, default=120)
    args = parser.parse_args()

    configure_logging()
    start_ts = parse_date(args.start)
    end_ts = parse_date(args.end) + 86400

    # symbols
    settings = get_settings()
    ex = WallexExchange.create(settings)
    try:
        if args.symbols:
            symbols = [s.strip() for s in args.symbols.split(",") if s.strip()]
        else:
            bot = NooaahBot(exchange=ex, config=NooaahConfig())
            symbols = await bot.pick_top_symbols(args.top)

        print(f"📥 Fetching {args.limit} candles for {len(symbols)} symbols...")
        uc = GetCandlesUseCase(exchange=ex)
        data: dict[str, list[Candle]] = {}
        for sym in symbols:
            c = await fetch_one(uc, sym, args.limit)
            if c:
                data[sym] = c
                print(f"  ✅ {sym}: {len(c)} candles")
            else:
                print(f"  ❌ {sym}: no data")
    finally:
        await ex.aclose()

    cfg = NooaahConfig(
        top_n=1,
        min_confidence=args.conf,
        tp_atr_mult=args.tp,
        sl_atr_mult=args.sl,
        confirmation_candles=args.cc,
    )

    results: list[SymbolResult] = []
    for sym, candles in data.items():
        try:
            s_idx, e_idx = find_idx_range(candles, start_ts, end_ts)
        except ValueError as e:
            results.append(SymbolResult(
                symbol=sym, trades=0, wins=0, losses=0, win_rate=0,
                total_return=0, max_dd=0, profit_factor=0, sharpe=0,
                avg_duration=0, buy_hold=0, error=str(e),
            ))
            continue

        if e_idx - s_idx < 50 or s_idx < args.warmup:
            results.append(SymbolResult(
                symbol=sym, trades=0, wins=0, losses=0, win_rate=0,
                total_return=0, max_dd=0, profit_factor=0, sharpe=0,
                avg_duration=0, buy_hold=0,
                error=f"window too small [{s_idx}:{e_idx}]",
            ))
            continue

        try:
            stats = run_nooaah_backtest(
                {sym: candles}, cfg,
                warmup=args.warmup,
                start_idx=s_idx,
                end_idx=e_idx,
            )
            bh = (
                (stats.buy_hold_curve[-1] - 100.0)
                if stats.buy_hold_curve else 0.0
            )
            results.append(SymbolResult(
                symbol=sym,
                trades=stats.total_trades,
                wins=stats.wins,
                losses=stats.losses,
                win_rate=stats.win_rate,
                total_return=stats.total_return_pct,
                max_dd=stats.max_drawdown_pct,
                profit_factor=stats.profit_factor,
                sharpe=stats.sharpe_ratio,
                avg_duration=stats.avg_duration_candles,
                buy_hold=bh,
            ))
        except ValueError as e:
            results.append(SymbolResult(
                symbol=sym, trades=0, wins=0, losses=0, win_rate=0,
                total_return=0, max_dd=0, profit_factor=0, sharpe=0,
                avg_duration=0, buy_hold=0, error=str(e),
            ))

    print_report(results, args.start, args.end, cfg)


if __name__ == "__main__":
    asyncio.run(main())
