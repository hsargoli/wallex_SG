"""Nooaah grid search with 70/30 train/test split.

هدف: پیدا کردن بهترین پارامترها روی TRAIN، تأیید روی TEST.

Usage (from ~/wallex/backend):
    uv run python -m scripts.nooaah_grid_search
"""

from __future__ import annotations

import argparse
import asyncio
import itertools
import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Sequence

from app.application.use_cases.get_candles import GetCandlesUseCase
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.domain.entities.candle import Candle
from app.infrastructure.exchange.wallex.client import WallexExchange
from app.services.bots.nooaah.backtest import run_nooaah_backtest
from app.services.bots.nooaah.bot import NooaahBot
from app.services.bots.nooaah.config import NooaahConfig

TRAIN_FILE = Path("data/nooaah_grid_train.json")
TEST_FILE = Path("data/nooaah_grid_test.json")


@dataclass(slots=True)
class GridRow:
    top_n: int
    min_confidence: int
    tp_atr_mult: float
    sl_atr_mult: float
    confirmation_candles: int
    trades: int
    win_rate: float
    total_return: float
    max_dd: float
    profit_factor: float
    sharpe: float

    def score(self) -> float:
        """امتیاز ترکیبی (fix شده)."""
        if self.trades < 5:
            return -999.0
        if self.max_dd < 0.01:  # guard divide-by-zero
            return -999.0
        calmar = self.total_return / self.max_dd
        sharpe_bonus = 1.0 + min(max(self.sharpe, 0.0), 1.0)
        return calmar * sharpe_bonus


def _to_row(
    tn: int, conf: int, tp: float, sl: float, cc: int, stats
) -> GridRow:
    return GridRow(
        top_n=tn,
        min_confidence=conf,
        tp_atr_mult=tp,
        sl_atr_mult=sl,
        confirmation_candles=cc,
        trades=stats.total_trades,
        win_rate=stats.win_rate,
        total_return=stats.total_return_pct,
        max_dd=stats.max_drawdown_pct,
        profit_factor=stats.profit_factor,
        sharpe=stats.sharpe_ratio,
    )


async def fetch_candles(
    symbols: list[str], limit: int
) -> dict[str, Sequence[Candle]]:
    settings = get_settings()
    ex = WallexExchange.create(settings)
    try:
        uc = GetCandlesUseCase(exchange=ex)
        cache: dict[str, Sequence[Candle]] = {}
        for sym in symbols:
            try:
                c = await uc.execute(symbol=sym, timeframe="1h", limit=limit)
                if c:
                    cache[sym] = c
                    print(f"  ✅ {sym}: {len(c)} candles")
            except Exception as e:
                print(f"  ❌ {sym}: {e}")
        return cache
    finally:
        await ex.aclose()


def split_train_test(
    candles: dict[str, Sequence[Candle]], train_pct: float = 0.7
) -> tuple[dict[str, Sequence[Candle]], dict[str, Sequence[Candle]]]:
    """تقسیم per-symbol: 70٪ اول train، 30٪ آخر test."""
    train: dict[str, Sequence[Candle]] = {}
    test: dict[str, Sequence[Candle]] = {}
    for sym, c in candles.items():
        split_at = int(len(c) * train_pct)
        train[sym] = c[:split_at]
        test[sym] = c[split_at:]
    return train, test


def run_grid_on(
    candles: dict[str, Sequence[Candle]],
    top_n_values: list[int],
    conf_values: list[int],
    tp_values: list[float],
    sl_values: list[float],
    confirmation_values: list[int],
    label: str,
    warmup: int = 200,
) -> list[GridRow]:
    total = (
        len(top_n_values) * len(conf_values) * len(tp_values)
        * len(sl_values) * len(confirmation_values)
    )
    print(f"\n🔍 [{label}] {total} combinations")

    symbols = list(candles.keys())
    results: list[GridRow] = []
    t0 = time.monotonic()

    for i, (tn, conf, tp, sl, cc) in enumerate(
        itertools.product(
            top_n_values, conf_values, tp_values, sl_values, confirmation_values
        )
    ):
        used = {s: candles[s] for s in symbols[:tn]}
        cfg = NooaahConfig(
            top_n=tn,
            min_confidence=conf,
            tp_atr_mult=tp,
            sl_atr_mult=sl,
            confirmation_candles=cc,
        )
        try:
            stats = run_nooaah_backtest(used, cfg, warmup=warmup)
            results.append(_to_row(tn, conf, tp, sl, cc, stats))
        except Exception:
            continue

        if (i + 1) % 30 == 0:
            elapsed = time.monotonic() - t0
            print(f"   {i + 1}/{total}  ({elapsed:.0f}s)")

    return results


def print_top(
    results: list[GridRow], label: str, n: int = 5
) -> None:
    scored = sorted(results, key=lambda r: r.score(), reverse=True)
    print(f"\n{'=' * 100}")
    print(f"  🏆 Top {n} by composite score — {label}")
    print(f"{'=' * 100}")
    print(
        f"  {'top':>4} {'conf':>5} {'tp':>5} {'sl':>5} {'cc':>4} | "
        f"{'trades':>7} {'WR%':>6} {'ret%':>8} {'DD%':>6} "
        f"{'PF':>5} {'Sharpe':>7}"
    )
    print("-" * 100)
    for r in scored[:n]:
        print(
            f"  {r.top_n:>4} {r.min_confidence:>5} "
            f"{r.tp_atr_mult:>5.1f} {r.sl_atr_mult:>5.1f} "
            f"{r.confirmation_candles:>4} | "
            f"{r.trades:>7} {r.win_rate:>6.1f} {r.total_return:>+8.2f} "
            f"{r.max_dd:>6.2f} {r.profit_factor:>5.2f} {r.sharpe:>7.3f}"
        )


def check_zombies(rows: list[GridRow]) -> None:
    """چک کن کدوم پارامترها تأثیر ندارن (زامبی).

    اگه تغییر یه پارامتر، نتیجه‌ی یهسان بده → زامبی.
    """
    if not rows:
        return
    print(f"\n{'=' * 100}")
    print(f"  🧟 Zombie parameter check")
    print(f"{'=' * 100}")

    # برای هر پارامتر: آیا unique results داره؟
    for param_name in ("top_n", "min_confidence", "tp_atr_mult", "sl_atr_mult", "confirmation_candles"):
        # گروه‌بندی بر اساس سایر پارامترها
        groups: dict[tuple, set] = {}
        for r in rows:
            key = tuple(
                getattr(r, k) for k in
                ("top_n", "min_confidence", "tp_atr_mult", "sl_atr_mult")
                if k != param_name
            )
            groups.setdefault(key, set()).add(getattr(r, param_name))
        unique_vals = len({getattr(r, param_name) for r in rows})
        print(f"   {param_name:20} unique values: {unique_vals}")
    print(f"   (اگه یه پارامتر 1 unique result بده → زامبی)")


def save(rows: list[GridRow], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps([asdict(r) for r in rows], indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"  💾 {len(rows)} rows → {path}")


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=500)
    parser.add_argument("--max-symbols", type=int, default=8)
    parser.add_argument("--train-pct", type=float, default=0.7)
    parser.add_argument("--warmup", type=int, default=200)
    args = parser.parse_args()

    configure_logging()
    settings = get_settings()
    ex = WallexExchange.create(settings)

    try:
        bot = NooaahBot(exchange=ex, config=NooaahConfig())
        symbols = await bot.pick_top_symbols(args.max_symbols)
        print(f"📥 Top {len(symbols)} symbols: {symbols}\n")
    finally:
        await ex.aclose()

    print(f"📥 Fetching {args.limit} candles per symbol...")
    candles = await fetch_candles(symbols, args.limit)
    if not candles:
        print("❌ no data")
        return

    train, test = split_train_test(candles, args.train_pct)
    split_at = int(args.limit * args.train_pct)

    # pre-check: test باید > warmup + 50 باشه
    WARMUP = args.warmup
    MIN = WARMUP + 51
    test_min = min(len(c) for c in test.values())
    print(f"\n📊 Split per symbol: {split_at} train / {args.limit - split_at} test")
    print(f"   test min size: {test_min} (need ≥ {MIN})")
    if test_min < MIN:
        min_limit = int(MIN / (1 - args.train_pct)) + 1
        raise SystemExit(
            f"❌ test set too small ({test_min} < {MIN}). "
            f"Use --limit ≥ {min_limit}"
        )

    # grid کوچک: 3×1×2×1×3 = 18 combos (شروع سریع)
    top_n_values = [3, 5, 8]
    conf_values = [55]
    tp_values = [3.0, 8.0]
    sl_values = [1.5]
    confirmation_values = [1, 2, 3]

    # ---- grid روی TRAIN ----
    train_rows = run_grid_on(
        train, top_n_values, conf_values, tp_values, sl_values,
        confirmation_values, "TRAIN",
        warmup=args.warmup,
    )
    print_top(train_rows, "TRAIN", n=5)
    check_zombies(train_rows)
    save(train_rows, TRAIN_FILE)

    # ---- بهترین config روی TRAIN ----
    best = max(train_rows, key=lambda r: r.score())
    print(f"\n{'=' * 100}")
    print(f"  🎯 Best config (TRAIN):")
    print(f"     top_n={best.top_n}  conf={best.min_confidence}  "
          f"tp={best.tp_atr_mult}  sl={best.sl_atr_mult}")
    print(f"     train: ret={best.total_return:+.2f}%  DD={best.max_dd:.2f}%  "
          f"sharpe={best.sharpe:.3f}  trades={best.trades}")
    print(f"{'=' * 100}")

    # ---- ارزیابی روی TEST ----
    print(f"\n🧪 Evaluating on TEST...")
    test_used = {s: test[s] for s in list(test.keys())[:best.top_n]}
    test_cfg = NooaahConfig(
        top_n=best.top_n,
        min_confidence=best.min_confidence,
        tp_atr_mult=best.tp_atr_mult,
        sl_atr_mult=best.sl_atr_mult,
        confirmation_candles=best.confirmation_candles,
    )
    test_stats = run_nooaah_backtest(test_used, test_cfg, warmup=args.warmup)
    test_row = _to_row(
        best.top_n, best.min_confidence, best.tp_atr_mult, best.sl_atr_mult,
        best.confirmation_candles, test_stats,
    )
    save([test_row], TEST_FILE)

    print(f"\n{'=' * 100}")
    print(f"  📊 Train vs Test")
    print(f"{'=' * 100}")
    print(f"  {'':12} {'trades':>8} {'WR%':>7} {'ret%':>8} "
          f"{'DD%':>7} {'PF':>6} {'Sharpe':>8}")
    print("-" * 100)
    print(
        f"  {'TRAIN':12} {best.trades:>8} {best.win_rate:>7.1f} "
        f"{best.total_return:>+8.2f} {best.max_dd:>7.2f} "
        f"{best.profit_factor:>6.2f} {best.sharpe:>8.3f}"
    )
    print(
        f"  {'TEST':12} {test_row.trades:>8} {test_row.win_rate:>7.1f} "
        f"{test_row.total_return:>+8.2f} {test_row.max_dd:>7.2f} "
        f"{test_row.profit_factor:>6.2f} {test_row.sharpe:>8.3f}"
    )

    # ---- verdict ----
    print(f"\n{'=' * 100}")
    if test_row.trades < 3:
        verdict = "⚠️  TEST: trades کم — نتیجه قابل اعتماد نیست"
    elif test_row.total_return >= best.total_return * 0.5:
        verdict = "✅ TEST نزدیک TRAIN — config قابل اعتماد"
    elif test_row.total_return > 0:
        verdict = "🟡 TEST مثبت ولی ضعیف‌تر — احتمال overfit ملایم"
    else:
        verdict = "❌ TEST منفی — overfit جدی، config دوم رو امتحان کن"
    print(f"  {verdict}")
    print(f"{'=' * 100}")


if __name__ == "__main__":
    asyncio.run(main())
