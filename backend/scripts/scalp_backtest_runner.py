"""Scalp Master backtest runner (CSV → per-period report + B&H/Cash baseline).

Usage:
    python scripts/scalp_backtest_runner.py \
        --csv data/candles/historical/BTCUSDT_1h.csv \
        --period 2022-04-01:2022-07-01 \
        --period 2023-10-01:2024-01-01 \
        --initial-capital 1000000
"""
from __future__ import annotations
import argparse, csv, sys
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

# Bootstrap: allow running `python scripts/scalp_backtest_runner.py` from backend/
_BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

from app.domain.entities.candle import Candle


def load_candles_csv(path: Path) -> list[Candle]:
    out: list[Candle] = []
    with path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            out.append(Candle(
                time=int(row["open_time"]),
                open=Decimal(str(row["open"])),
                high=Decimal(str(row["high"])),
                low=Decimal(str(row["low"])),
                close=Decimal(str(row["close"])),
                volume=Decimal(str(row["volume"])),
            ))
    return out


def filter_by_date(candles: list[Candle], start_ts: int, end_ts: int) -> list[Candle]:
    return [c for c in candles if start_ts <= c.time <= end_ts]


def buy_and_hold(candles: list[Candle], initial_capital: float, fee_pct: float = 0.2) -> dict:
    if not candles:
        return {"total_pnl": 0.0, "total_pnl_pct": 0.0, "final_capital": initial_capital}
    fee = fee_pct / 100
    entry = float(candles[0].close)
    exit_ = float(candles[-1].close)
    units = initial_capital * (1 - fee) / entry   # fee on buy
    final = units * exit_ * (1 - fee)             # fee on sell
    pnl = final - initial_capital
    return {
        "total_pnl": round(pnl, 2),
        "total_pnl_pct": round(pnl / initial_capital * 100, 2) if initial_capital else 0.0,
        "final_capital": round(final, 2),
    }


def cash_baseline(initial_capital: float) -> dict:
    return {"total_pnl": 0.0, "total_pnl_pct": 0.0, "final_capital": initial_capital}


def _parse_period(s: str) -> tuple[int, int]:
    a, b = s.split(":")
    def _ts(d: str) -> int:
        dt = datetime.fromisoformat(d).replace(tzinfo=timezone.utc)
        return int(dt.timestamp())
    return _ts(a), _ts(b)


def run_period(candles: list[Candle], label: str, initial_capital: float,
               fee_pct: float, slippage_pct: float, spread_pct: float,
               config=None) -> dict:
    from app.infrastructure.backtest.bot_backtest import run_scalp_backtest
    bt = run_scalp_backtest(
        candles,
        initial_capital=initial_capital,
        position_size_pct=50.0,
        fee_pct=fee_pct,
        slippage_pct=slippage_pct,
        spread_pct=spread_pct,
        config=config,
    )
    bh = buy_and_hold(candles, initial_capital, fee_pct=fee_pct)
    cash = cash_baseline(initial_capital)
    return {
        "label": label,
        "candles": len(candles),
        "bot": {
            "trades": bt["total_trades"],
            "win_rate": bt["win_rate"],
            "pnl": bt["total_pnl"],
            "pnl_pct": bt["total_pnl_pct"],
            "profit_factor": bt["profit_factor"],
            "max_dd_pct": bt["max_drawdown_pct"],
        },
        "buy_hold": bh,
        "cash": cash,
        "edge_vs_bh_pct": round(bt["total_pnl_pct"] - bh["total_pnl_pct"], 2),
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True)
    ap.add_argument("--period", action="append", required=True,
                    help="START:END (ISO date), can repeat")
    ap.add_argument("--initial-capital", type=float, default=1_000_000.0)
    ap.add_argument("--fee-pct", type=float, default=0.2)
    ap.add_argument("--slippage-pct", type=float, default=0.1)
    ap.add_argument("--spread-pct", type=float, default=0.05)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    candles_all = load_candles_csv(Path(args.csv))
    results = []
    from app.services.bots.scalp_master.config import ScalpMasterConfig
    cfg = ScalpMasterConfig(watchlist_enabled=True, trend_filter_enabled=True)

    for p in args.period:
        s_ts, e_ts = _parse_period(p)
        sub = filter_by_date(candles_all, s_ts, e_ts)
        results.append(run_period(sub, p, args.initial_capital,
                                  args.fee_pct, args.slippage_pct, args.spread_pct,
                                  config=cfg))

    if args.json:
        import json as _json
        print(_json.dumps(results, ensure_ascii=False, indent=2))
        return 0

    print("=" * 78)
    print(f"SCALP MASTER BACKTEST — {Path(args.csv).name}")
    print(f"Costs: fee={args.fee_pct}%  slip={args.slippage_pct}%  spread={args.spread_pct}%")
    print("=" * 78)
    for r in results:
        print(f"\n>> {r['label']}  ({r['candles']} candles)")
        b = r["bot"]
        print(f"   bot     : trades={b['trades']:>4}  win={b['win_rate']:>5}%  "
              f"PnL={b['pnl']:>+12,.0f} ({b['pnl_pct']:>+6.2f}%)  PF={b['profit_factor']}  DD={b['max_dd_pct']}%")
        print(f"   buy&hold: PnL={r['buy_hold']['total_pnl']:>+12,.0f} ({r['buy_hold']['total_pnl_pct']:>+6.2f}%)")
        print(f"   cash    : PnL={r['cash']['total_pnl']:>+12,.0f} ({r['cash']['total_pnl_pct']:>+6.2f}%)")
        print(f"   edge vs B&H: {r['edge_vs_bh_pct']:>+6.2f}%")
    print("\n" + "=" * 78)
    return 0


if __name__ == "__main__":
    sys.exit(main())
