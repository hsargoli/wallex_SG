"""SarvTiger backtest on BTC 1h → resampled 4h."""
import argparse, csv, sys
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

_BACKEND = Path(__file__).resolve().parent.parent
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from app.domain.entities.candle import Candle
from app.services.bots.sarv_tiger.config import SarvTigerConfig
from app.services.bots.sarv_tiger.strategy import evaluate_entry, evaluate_exit

DATA = _BACKEND / "data" / "candles" / "historical" / "BTCUSDT_1h.csv"


def load_1h(path):
    out = []
    with open(path) as f:
        for row in csv.DictReader(f):
            ts = int(row["open_time"])
            if ts > 10_000_000_000:
                ts //= 1000
            out.append(Candle(
                time=ts, open=Decimal(row["open"]), high=Decimal(row["high"]),
                low=Decimal(row["low"]), close=Decimal(row["close"]),
                volume=Decimal(row["volume"]),
            ))
    return out


def resample_4h(c1h):
    out = []
    for i in range(0, len(c1h), 4):
        chunk = c1h[i:i+4]
        if len(chunk) < 4:
            break
        out.append(Candle(
            time=chunk[0].time,
            open=chunk[0].open,
            high=max(c.high for c in chunk),
            low=min(c.low for c in chunk),
            close=chunk[-1].close,
            volume=sum((c.volume for c in chunk), Decimal("0")),
        ))
    return out


def run_backtest(candles, config, initial_capital=1_000_000.0,
                 fee_pct=0.05, slippage_pct=0.05):
    fee = fee_pct / 100.0
    slip = slippage_pct / 100.0
    capital = initial_capital
    peak = initial_capital
    max_dd = 0.0
    trades = []
    position = None
    warmup = max(config.bb_period, config.atr_period) + config.bb_squeeze_window + 5

    for i in range(warmup, len(candles)):
        window = candles[:i+1]
        c = candles[i]

        if position is not None:
            should_exit, exit_px, reason = evaluate_exit(
                window, position["entry"], position["sl"], position["tp"], config
            )
            if should_exit:
                # exit with slippage (unfavorable)
                exit_net = exit_px * (1 - fee - slip)
                entry_net = position["entry"] * (1 + fee + slip)
                pnl = (exit_net - entry_net) * position["qty"]
                capital += pnl
                trades.append({
                    "entry": entry_net, "exit": exit_net,
                    "pnl": pnl, "pnl_pct": pnl / (entry_net * position["qty"]) * 100,
                    "reason": reason,
                })
                position = None
                peak = max(peak, capital)
                if peak > 0:
                    max_dd = max(max_dd, (peak - capital) / peak * 100)
        else:
            sig = evaluate_entry(window, config)
            if sig:
                # allocate
                size_tmn = capital * (config.position_size_pct / 100.0) * config.leverage
                qty = size_tmn / sig["entry"]
                position = {
                    "entry": sig["entry"],
                    "sl": sig["sl"],
                    "tp": sig["tp"],
                    "qty": qty,
                }

    # close at end
    if position is not None:
        exit_px = float(candles[-1].close)
        exit_net = exit_px * (1 - fee - slip)
        entry_net = position["entry"] * (1 + fee + slip)
        pnl = (exit_net - entry_net) * position["qty"]
        capital += pnl
        trades.append({"entry": entry_net, "exit": exit_net,
                       "pnl": pnl, "pnl_pct": pnl / (entry_net * position["qty"]) * 100,
                       "reason": "end_of_data"})

    wins = [t for t in trades if t["pnl"] > 0]
    losses = [t for t in trades if t["pnl"] <= 0]
    gw = sum(t["pnl"] for t in wins) if wins else 0
    gl = abs(sum(t["pnl"] for t in losses)) if losses else 0

    return {
        "candles_4h": len(candles),
        "trades": len(trades),
        "wins": len(wins),
        "losses": len(losses),
        "win_rate_pct": round(len(wins) / len(trades) * 100, 1) if trades else 0.0,
        "avg_win": round(sum(t["pnl"] for t in wins) / len(wins), 0) if wins else 0,
        "avg_loss": round(sum(t["pnl"] for t in losses) / len(losses), 0) if losses else 0,
        "total_pnl": round(capital - initial_capital, 0),
        "total_pnl_pct": round((capital / initial_capital - 1) * 100, 2),
        "profit_factor": round(gw / gl, 2) if gl > 0 else None,
        "max_dd_pct": round(max_dd, 1),
        "avg_exit_reason": {r: sum(1 for t in trades if t["reason"] == r)
                            for r in ("stop_loss", "take_profit", "end_of_data")},
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default=str(DATA))
    ap.add_argument("--leverage", type=int, default=None)
    ap.add_argument("--position", type=float, default=None)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    cfg = SarvTigerConfig()
    if args.leverage is not None:
        cfg.leverage = args.leverage
        cfg.max_leverage = max(cfg.max_leverage, args.leverage)
    if args.position is not None:
        cfg.position_size_pct = args.position

    print(f"CONFIG: leverage={cfg.leverage}x, position={cfg.position_size_pct}%, "
          f"sl={cfg.sl_atr_mult}ATR, tp={cfg.tp_atr_mult}ATR")

    c1h = load_1h(Path(args.csv))
    c4h = resample_4h(c1h)
    print(f"Loaded {len(c1h)} 1h candles → {len(c4h)} 4h candles")

    r = run_backtest(c4h, cfg)
    print(f"\n=== BACKTEST RESULT ===")
    print(f"Trades: {r['trades']}  (wins={r['wins']}, losses={r['losses']})")
    print(f"Win rate: {r['win_rate_pct']}%")
    print(f"Total PnL: {r['total_pnl']:+,.0f} TMN ({r['total_pnl_pct']:+.2f}%)")
    print(f"Profit factor: {r['profit_factor']}")
    print(f"Max DD: {r['max_dd_pct']}%")
    print(f"Exit reasons: {r['avg_exit_reason']}")
    if r["trades"] > 0:
        expectancy = r["total_pnl"] / r["trades"]
        print(f"Expectancy per trade: {expectancy:+,.0f} TMN")


if __name__ == "__main__":
    main()
