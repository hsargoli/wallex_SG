"""Paper trading report for scalp_master. Usage: python scripts/scalp_paper_report.py"""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
from typing import Any, Iterable


def build_report(trades: Iterable[dict], *, capital_start: float) -> dict[str, Any]:
    trades = list(trades)
    n = len(trades)
    if n == 0:
        return {
            "total_trades": 0, "wins": 0, "losses": 0, "win_rate_pct": 0.0,
            "avg_win": 0.0, "avg_loss": 0.0, "profit_factor": 0.0,
            "total_pnl": 0.0, "best_trade": 0.0, "worst_trade": 0.0,
            "max_drawdown_pct": 0.0, "by_reason": {},
            "final_capital": capital_start, "equity_curve": [capital_start],
        }
    pnls = [float(t.get("pnl_net", 0.0)) for t in trades]
    wins = [p for p in pnls if p > 0]
    losses = [p for p in pnls if p < 0]
    by_reason: dict[str, int] = {}
    for t in trades:
        r = t.get("exit_reason", "unknown")
        by_reason[r] = by_reason.get(r, 0) + 1
    equity = [float(capital_start)]
    for p in pnls:
        equity.append(equity[-1] + p)
    peak, max_dd = equity[0], 0.0
    for v in equity:
        if v > peak: peak = v
        dd = (v - peak) / peak * 100.0 if peak > 0 else 0.0
        if dd < max_dd: max_dd = dd
    total_pnl = sum(pnls)
    gross_win = sum(wins) if wins else 0.0
    gross_loss = abs(sum(losses)) if losses else 0.0
    pf = (gross_win / gross_loss) if gross_loss > 0 else (None if gross_win == 0 else None)
    return {
        "total_trades": n, "wins": len(wins), "losses": len(losses),
        "win_rate_pct": round(len(wins) / n * 100.0, 2),
        "avg_win": round(sum(wins) / len(wins), 2) if wins else 0.0,
        "avg_loss": round(sum(losses) / len(losses), 2) if losses else 0.0,
        "profit_factor": round(pf, 2) if pf is not None else None,
        "total_pnl": round(total_pnl, 2),
        "best_trade": round(max(pnls), 2),
        "worst_trade": round(min(pnls), 2),
        "max_drawdown_pct": round(max_dd, 4),
        "by_reason": dict(sorted(by_reason.items(), key=lambda kv: -kv[1])),
        "final_capital": round(equity[-1], 2),
        "equity_curve": [round(v, 2) for v in equity],
    }


def collect_trades(data_dir: Path, user_id: str | None = None) -> list[dict]:
    out: list[dict] = []
    if not data_dir.exists(): return out
    files = sorted(data_dir.glob("*.json"))
    if user_id: files = [f for f in files if f.stem == user_id]
    for f in files:
        try: d = json.loads(f.read_text(encoding="utf-8"))
        except Exception: continue
        for t in d.get("closed_trades", []) or []:
            t = dict(t); t["_user_id"] = f.stem; out.append(t)
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default="data/bots/scalp_master/users")
    ap.add_argument("--user-id", default=None)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--capital-start", type=float, default=300_000.0)
    args = ap.parse_args(argv)
    trades = collect_trades(Path(args.data_dir), args.user_id)
    r = build_report(trades, capital_start=args.capital_start)
    if args.json:
        print(json.dumps(r, ensure_ascii=False, indent=2)); return 0
    print("=" * 60); print("SCALP MASTER — PAPER REPORT"); print("=" * 60)
    print(f"Total trades : {r['total_trades']}")
    print(f"Wins / Losses: {r['wins']} / {r['losses']}")
    print(f"Win rate     : {r['win_rate_pct']}%")
    print(f"Avg win      : {r['avg_win']:+,.0f} TMN")
    print(f"Avg loss     : {r['avg_loss']:+,.0f} TMN")
    print(f"Profit factor: {r['profit_factor'] if r['profit_factor'] is not None else 'inf'}")
    print(f"Total PnL    : {r['total_pnl']:+,.0f} TMN")
    print(f"Best / Worst : {r['best_trade']:+,.0f} / {r['worst_trade']:+,.0f} TMN")
    print(f"Max drawdown : {r['max_drawdown_pct']}%")
    print(f"Final capital: {r['final_capital']:,.0f} TMN")
    if r["by_reason"]:
        print("-" * 60); print("By exit reason:")
        for k, v in r["by_reason"].items(): print(f"  {k:14s}: {v}")
    print("=" * 60); return 0


if __name__ == "__main__":
    sys.exit(main())
