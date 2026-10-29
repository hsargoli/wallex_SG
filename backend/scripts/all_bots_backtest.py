"""Run all bots backtests on standard periods. Compares PF, Win%, PnL, DD."""
from __future__ import annotations
import argparse, csv, sys
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

_BACKEND = Path(__file__).resolve().parent.parent
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from app.domain.entities.candle import Candle

PERIODS = {
    "Q2-2022": ("2022-04-01", "2022-07-01"),
    "Q4-2023": ("2023-10-01", "2024-01-01"),
    "Q1-2024": ("2024-01-01", "2024-04-01"),
}

DATA_DIR = _BACKEND / "data" / "candles" / "historical"


def _ts(s: str) -> int:
    return int(datetime.fromisoformat(s).replace(tzinfo=timezone.utc).timestamp())


def _load_candles_csv(path: Path, start: str, end: str) -> list[Candle]:
    s_ts, e_ts = _ts(start), _ts(end)
    out: list[Candle] = []
    with path.open("r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            ts = int(row["open_time"])
            if ts > 10_000_000_000:
                ts //= 1000
            if s_ts <= ts < e_ts:
                out.append(Candle(
                    time=ts,
                    open=Decimal(str(row["open"])),
                    high=Decimal(str(row["high"])),
                    low=Decimal(str(row["low"])),
                    close=Decimal(str(row["close"])),
                    volume=Decimal(str(row["volume"])),
                ))
    return out


# ─── Standardizers ──────────────────────────────────────────────────

def standardize_nooaah(period: str, r) -> dict:
    return {
        "bot": "nooaah", "period": period,
        "trades": getattr(r, "total_trades", 0),
        "win_rate": round(getattr(r, "win_rate", 0.0), 2),
        "pnl_pct": round(getattr(r, "total_return_pct", 0.0), 2),
        "pf": round(getattr(r, "profit_factor", 0.0), 2) or None,
        "max_dd_pct": round(getattr(r, "max_drawdown_pct", 0.0), 2),
    }


# ─── Runners ────────────────────────────────────────────────────────

def run_nooaah(period: str) -> dict:
    from app.services.bots.nooaah.backtest import run_nooaah_backtest
    from app.services.bots.nooaah.config import NooaahConfig
    start, end = PERIODS[period]
    syms = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
    candles_by_sym = {}
    for s in syms:
        p = DATA_DIR / f"{s}_1h.csv"
        if p.exists():
            cs = _load_candles_csv(p, start, end)
            if cs:
                candles_by_sym[s] = cs
    if not candles_by_sym:
        return {"bot": "nooaah", "period": period,
                "trades": 0, "win_rate": 0.0, "pnl_pct": 0.0,
                "pf": None, "max_dd_pct": 0.0, "error": "no data"}
    try:
        r = run_nooaah_backtest(candles_by_sym, NooaahConfig())
        return standardize_nooaah(period, r)
    except Exception as e:
        return {"bot": "nooaah", "period": period,
                "trades": 0, "win_rate": 0.0, "pnl_pct": 0.0,
                "pf": None, "max_dd_pct": 0.0, "error": f"{type(e).__name__}: {e}"}


BOT_RUNNERS = {"nooaah": run_nooaah}


def run_all(periods: list[str] | None = None) -> list[dict]:
    if periods is None:
        periods = list(PERIODS.keys())
    rows = []
    for bot_name, fn in BOT_RUNNERS.items():
        for p in periods:
            try:
                rows.append(fn(p))
            except Exception as e:
                rows.append({"bot": bot_name, "period": p,
                             "trades": 0, "win_rate": 0.0, "pnl_pct": 0.0,
                             "pf": None, "max_dd_pct": 0.0,
                             "error": f"{type(e).__name__}: {e}"})
    return rows


def _fmt_pf(pf) -> str:
    return f"{pf:.2f}" if isinstance(pf, (int, float)) else "  - "


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--period", action="append", default=None,
                    help="Q2-2022 / Q4-2023 / Q1-2024 (default: all)")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    rows = run_all(args.period)

    if args.json:
        import json as _j
        print(_j.dumps(rows, ensure_ascii=False, indent=2, default=str))
        return 0

    print("=" * 90)
    print("ALL-BOTS BACKTEST")
    print("=" * 90)
    print(f"{'Bot':<14} {'Period':<10} {'Trades':>7} {'Win%':>7} {'PnL%':>9} {'PF':>6} {'DD%':>7} Note")
    print("-" * 90)
    for r in rows:
        note = r.get("error", "")[:30] if "error" in r else ""
        print(f"{r['bot']:<14} {r['period']:<10} {r['trades']:>7} "
              f"{r['win_rate']:>6.1f}% {r['pnl_pct']:>+8.2f}% "
              f"{_fmt_pf(r['pf']):>6} {r['max_dd_pct']:>6.1f}% {note}")
    print("=" * 90)
    return 0


if __name__ == "__main__":
    sys.exit(main())
