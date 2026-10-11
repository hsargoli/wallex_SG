"""Nooaah Time Machine — backtest on a specific date range.

Usage (from ~/wallex/backend):
    uv run python -m scripts.nooaah_time_machine --start 2026-09-15 --end 2026-10-10
    uv run python -m scripts.nooaah_time_machine --start 2026-09-15 --end 2026-10-10 --symbols BTCTMN,ETHTMN
"""

from __future__ import annotations

import argparse
import asyncio
import csv
from datetime import datetime, timezone
from pathlib import Path

from app.application.use_cases.get_candles import GetCandlesUseCase
from app.core.config import get_settings
from app.core.logging import configure_logging
from decimal import Decimal

from app.domain.entities.candle import Candle
from app.infrastructure.exchange.wallex.client import WallexExchange
from app.services.bots.nooaah.backtest import run_nooaah_backtest
from app.services.bots.nooaah.bot import NooaahBot
from app.services.bots.nooaah.config import NooaahConfig


def load_1m_csv(symbol: str) -> list[Candle]:
    """بارگذاری 1m از CSV (اگه موجود)."""
    path = Path(__file__).resolve().parent.parent / "data" / "candles" / f"{symbol}_1m.csv"
    if not path.exists():
        return []
    out: list[Candle] = []
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        next(reader, None)  # header
        for row in reader:
            if len(row) == 6:
                try:
                    out.append(Candle(
                        time=int(row[0]),
                        open=Decimal(row[1]),
                        high=Decimal(row[2]),
                        low=Decimal(row[3]),
                        close=Decimal(row[4]),
                        volume=Decimal(row[5]),
                    ))
                except Exception:
                    continue
    return out


def parse_date(s: str) -> int:
    """ISO date (YYYY-MM-DD) → unix timestamp UTC."""
    dt = datetime.strptime(s, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    return int(dt.timestamp())


def fmt_dt(ts: int) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%m-%d %H:%M")


def fmt_money(v: float, capital: float) -> str:
    """نمایش مقدار به صورت درصدی از سرمایه اولیه + مقدار خام."""
    return f"{v:,.0f}"


async def fetch_all(
    symbols: list[str], limit: int
) -> dict[str, list[Candle]]:
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
                    print(f"  ✅ {sym}: {len(c)} candles")
            except Exception as e:
                print(f"  ❌ {sym}: {e}")
        return data
    finally:
        await ex.aclose()


def find_idx_range(
    candles: list[Candle], start_ts: int, end_ts: int
) -> tuple[int, int]:
    """پیدا کردن [start_idx, end_idx) که تو بازه‌ی [start_ts, end_ts) قرار دارن."""
    start_idx = None
    end_idx = len(candles)
    for i, c in enumerate(candles):
        if start_idx is None and c.time >= start_ts:
            start_idx = i
        if c.time >= end_ts:
            end_idx = i
            break
    if start_idx is None:
        raise ValueError(f"no candles after start")
    return start_idx, end_idx


def print_report(stats, capital: float, label: str) -> None:
    print()
    print("=" * 95)
    print(f"  📊 {label}")
    print("=" * 95)
    final_cap = capital * (1 + stats.total_return_pct / 100)
    print(f"  سرمایه اولیه:        {capital:>18,.0f}")
    print(f"  سرمایه نهایی:        {final_cap:>18,.0f}")
    print(f"  بازده:               {stats.total_return_pct:>+18.2f}%")
    print(f"  Max Drawdown:        {stats.max_drawdown_pct:>18.2f}%")
    print(f"  Sharpe:              {stats.sharpe_ratio:>18.3f}")
    print(f"  Profit Factor:       {stats.profit_factor:>18.2f}")
    print(f"  معاملات:             {stats.total_trades:>18}")
    print(f"  برد / باخت:          {stats.wins:>10} / {stats.losses}")
    print(f"  Win rate:            {stats.win_rate:>18.1f}%")
    print(f"  میانگین مدت:         {stats.avg_duration_candles:>16.1f}h")

    if stats.buy_hold_curve:
        bh = stats.buy_hold_curve[-1] - 100.0
        diff = stats.total_return_pct - bh
        marker = "✅" if diff > 0 else ("🟡" if diff > -3 else "⚠️")
        print(f"  خرید-و-نگه‌داری:    {bh:>+18.2f}%")
        print(f"  تفاوت با B&H:        {diff:>+18.2f}%  {marker}")


def print_trades(stats) -> None:
    if not stats.trades:
        print("\n  ❌ هیچ معامله‌ای انجام نشد")
        return
    print()
    print("=" * 95)
    print(f"  📅 معاملات ({len(stats.trades)})")
    print("=" * 95)
    print(
        f"  {'ورود':<13} {'نماد':<9} {'قیمت ورود':>14} {'قیمت خروج':>14} "
        f"{'دلیل':<11} {'بازده':>8} {'مدت':>5} {'conf':>5}"
    )
    print("-" * 95)
    for t in stats.trades:
        ret = t.return_pct
        icon = "🟢" if ret > 0 else "🔴"
        print(
            f"  {fmt_dt(t.entry_time):<13} {t.symbol:<9} "
            f"{float(t.entry_price):>14,.0f} {float(t.exit_price):>14,.0f} "
            f"{t.exit_reason:<11} {ret:>+7.2f}% {t.duration_candles:>4}h "
            f"{t.confidence:>4}% {icon}"
        )


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", required=True, help="YYYY-MM-DD (UTC)")
    parser.add_argument("--end", required=True, help="YYYY-MM-DD (UTC، inclusive)")
    parser.add_argument("--symbols", default=None, help="comma-separated")
    parser.add_argument("--top", type=int, default=5)
    parser.add_argument("--limit", type=int, default=700)
    parser.add_argument("--capital", type=float, default=100_000_000.0)
    parser.add_argument("--conf", type=int, default=60)
    parser.add_argument("--tp", type=float, default=3.0)
    parser.add_argument("--sl", type=float, default=1.5)
    parser.add_argument("--cc", type=int, default=2)
    parser.add_argument("--warmup", type=int, default=120)
    parser.add_argument("--momentum", type=int, default=0, help="window 1m for momentum exit (0=off)")
    parser.add_argument("--red-ratio", type=float, default=0.6)
    parser.add_argument("--mom-mode", default="ratio", choices=["ratio", "consecutive", "cumulative"])
    parser.add_argument("--vol-z-min", type=float, default=-10.0)
    parser.add_argument("--cooldown", type=int, default=0)
    parser.add_argument("--daily-loss-limit", type=float, default=100.0)
    parser.add_argument("--max-positions", type=int, default=1)
    parser.add_argument("--partial", action="store_true")
    parser.add_argument("--confirm-4h", action="store_true")
    parser.add_argument("--stale-hours", type=int, default=0)
    parser.add_argument("--stale-profit", type=float, default=0.5)
    parser.add_argument("--tp2-mult", type=float, default=5.0)
    parser.add_argument("--partial-fraction", type=float, default=0.5)
    parser.add_argument("--conf-sizing", action="store_true")
    parser.add_argument("--mult-low", type=float, default=0.7)
    parser.add_argument("--mult-high", type=float, default=1.5)
    parser.add_argument("--conf-low", type=int, default=80)
    parser.add_argument("--conf-high", type=int, default=95)
    parser.add_argument("--rsi-max", type=float, default=100.0)
    parser.add_argument("--rsi-min", type=float, default=0.0)
    parser.add_argument("--trailing", action="store_true", help="استفاده از Trailing ATR به‌جای TP")
    parser.add_argument("--trailing-mult", type=float, default=1.5)
    parser.add_argument("--mom-consecutive", type=int, default=4)
    parser.add_argument("--mom-cumulative-pct", type=float, default=-0.3)
    parser.add_argument("--regime-window", type=int, default=20)
    parser.add_argument("--regime-ratio", type=float, default=0.30)
    args = parser.parse_args()

    configure_logging()
    start_ts = parse_date(args.start)
    end_ts = parse_date(args.end) + 86400  # پایان روز end

    if end_ts <= start_ts:
        raise SystemExit("❌ end must be after start")

    # symbols
    if args.symbols:
        symbols = [s.strip() for s in args.symbols.split(",") if s.strip()]
    else:
        settings = get_settings()
        ex = WallexExchange.create(settings)
        try:
            bot = NooaahBot(exchange=ex, config=NooaahConfig())
            symbols = await bot.pick_top_symbols(args.top)
        finally:
            await ex.aclose()

    print()
    print("=" * 95)
    print(f"  🕰️  Nooaah Time Machine")
    print("=" * 95)
    print(f"  بازه:      {args.start} → {args.end}")
    print(f"  نمادها:    {', '.join(symbols)}")
    print(f"  سرمایه:    {args.capital:,.0f}")
    mom_str = f"mom={args.momentum}({args.red_ratio})" if args.momentum > 0 else "mom=off"
    rg_str = f"rg={args.regime_window}({args.regime_ratio})" if args.regime_window > 0 else "rg=off"
    tr_str = f"trailing={args.trailing_mult}" if args.trailing else "trailing=off"
    rsi_str = f"rsi=[{args.rsi_min},{args.rsi_max}]" if (args.rsi_max < 100 or args.rsi_min > 0) else "rsi=off"
    print(f"  پارامترها: conf={args.conf} tp={args.tp} sl={args.sl} cc={args.cc} {mom_str} {rg_str} {tr_str} {rsi_str}")

    print(f"\n📥 Fetching {args.limit} candles per symbol...")
    data = await fetch_all(symbols, args.limit)
    if not data:
        print("❌ no data")
        return

    # بارگذاری 1m (اگه momentum فعاله)
    candles_1m_by_symbol: dict[str, list[Candle]] = {}
    if args.momentum > 0:
        print(f"\n📥 Loading 1m candles for momentum exit (window={args.momentum})...")
        for sym in data.keys():
            m1 = load_1m_csv(sym)
            if m1:
                candles_1m_by_symbol[sym] = m1
                print(f"   {sym}: {len(m1)} 1m candles")

    # پیدا کردن idx range
    filtered_data: dict[str, list[Candle]] = {}
    start_idxs: list[int] = []
    end_idxs: list[int] = []
    for sym, candles in data.items():
        try:
            s_idx, e_idx = find_idx_range(candles, start_ts, end_ts)
            if e_idx - s_idx < 30:
                print(f"   ⚠️  {sym}: only {e_idx - s_idx} candles in range, skip")
                continue
            filtered_data[sym] = candles
            start_idxs.append(s_idx)
            end_idxs.append(e_idx)
            print(f"   {sym}: idx [{s_idx}:{e_idx}]  ({e_idx - s_idx} candles)")
        except ValueError as e:
            print(f"   ⚠️  {sym}: {e}")

    if not filtered_data:
        print("\n❌ هیچ نمادی تو بازه نیست")
        return

    # shared window (همه باید هم‌زمان کار کنن)
    effective_start = max(start_idxs)
    effective_end = min(end_idxs)

    if effective_start < args.warmup:
        raise SystemExit(
            f"❌ effective_start={effective_start} < warmup={args.warmup}. "
            f"بازه رو دیرتر شروع کن یا --limit بیشتر."
        )

    if effective_end - effective_start < 50:
        raise SystemExit(
            f"❌ window too small: [{effective_start}:{effective_end}]"
        )

    real_start = data[list(filtered_data)[0]][effective_start].time
    real_end = data[list(filtered_data)[0]][effective_end - 1].time

    print(f"\n   📅 پنجره‌ی موثر: {fmt_dt(real_start)} → {fmt_dt(real_end)}")
    print(f"      {effective_end - effective_start} کندل ({effective_end - effective_start} ساعت)")

    # backtest
    cfg = NooaahConfig(
        top_n=len(filtered_data),
        min_confidence=args.conf,
        tp_atr_mult=args.tp,
        sl_atr_mult=args.sl,
        confirmation_candles=args.cc,
        momentum_exit_candles=args.momentum,
        momentum_red_ratio=args.red_ratio,
        momentum_mode=args.mom_mode,
        momentum_consecutive=args.mom_consecutive,
        momentum_cumulative_pct=args.mom_cumulative_pct,
        regime_filter_window=args.regime_window,
        regime_filter_min_ratio=args.regime_ratio,
        use_trailing=args.trailing,
        trailing_atr_mult=args.trailing_mult,
        rsi_entry_max=args.rsi_max,
        rsi_entry_min=args.rsi_min,
        volume_z_min=args.vol_z_min,
        cooldown_after_sl=args.cooldown,
        daily_loss_limit=args.daily_loss_limit,
        max_concurrent_positions=args.max_positions,
        use_partial_exit=args.partial,
        use_4h_confirmation=args.confirm_4h,
        tp2_atr_mult=args.tp2_mult,
        partial_fraction=args.partial_fraction,
        stale_exit_hours=args.stale_hours,
        stale_exit_min_profit=args.stale_profit,
        use_confidence_sizing=args.conf_sizing,
        size_mult_low=args.mult_low,
        size_mult_high=args.mult_high,
        conf_sizing_low=args.conf_low,
        conf_sizing_high=args.conf_high,
    )

    stats = run_nooaah_backtest(
        filtered_data, cfg,
        warmup=args.warmup,
        start_idx=effective_start,
        end_idx=effective_end,
        candles_1m_by_symbol=candles_1m_by_symbol or None,
    )

    # گزارش
    label = f"دوره‌ی {args.start} → {args.end}"
    print_report(stats, args.capital, label)
    print_trades(stats)


if __name__ == "__main__":
    asyncio.run(main())
