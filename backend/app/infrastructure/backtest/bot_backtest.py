"""بک‌تست ربات scalp_master روی کندل‌های گذشته (بدون look-ahead)."""

from app.domain.entities.candle import Candle
from app.services.bots.scalp_master.config import ScalpMasterConfig
from app.services.bots.scalp_master.strategy import evaluate_entry, evaluate_exit


def run_scalp_backtest(
    candles: list[Candle],
    initial_capital: float = 1000.0,
    position_size_pct: float = 50.0,
    fee_pct: float = 0.2,
    slippage_pct: float = 0.1,
    spread_pct: float = 0.05,
    config: ScalpMasterConfig | None = None,
) -> dict:
    cfg = config or ScalpMasterConfig()
    fee = fee_pct / 100
    slippage = slippage_pct / 100
    half_spread = (spread_pct / 100) / 2.0
    entry_adj = fee + slippage + half_spread
    exit_adj = fee + slippage + half_spread

    cash = initial_capital
    pos: dict | None = None
    trades: list[dict] = []
    curve: list[dict] = []
    peak = initial_capital
    max_dd = 0.0
    signals = 0

    for i in range(cfg.warmup_candles, len(candles)):
        window = candles[: i + 1]  # فقط گذشته تا همین کندل
        c = candles[i]
        t = int(c.time)

        # ── خروج (از کندل بعد از ورود) ──
        if pos is not None:
            held = i - pos["idx"]
            done, px, reason = evaluate_exit(
                window, pos["entry"], pos["sl"], pos["tp"], held, cfg
            )
            if done:
                exit_net = px * (1 - exit_adj)
                revenue = pos["qty"] * exit_net
                cost = pos["qty"] * pos["entry"]
                pnl = revenue - cost
                cash += revenue
                trades.append({
                    "symbol": pos["symbol"],
                    "side": "BUY",
                    "entry_time": pos["time"],
                    "exit_time": t,
                    "entry_price": round(pos["entry"], 8),
                    "exit_price": round(exit_net, 8),
                    "quantity": pos["qty"],
                    "pnl": round(pnl, 4),
                    "pnl_pct": round(pnl / cost * 100, 2) if cost > 0 else 0,
                    "exit_reason": reason,
                    "duration_candles": held,
                })
                pos = None

        # ── ورود ──
        if pos is None:
            sig = evaluate_entry(window, cfg)
            if sig is not None and sig.should_trade:
                signals += 1
                size = cash * (position_size_pct / 100)
                entry_net = float(sig.entry_price) * (1 + entry_adj)
                if size > 0:
                    pos = {
                        "symbol": "",
                        "idx": i,
                        "time": t,
                        "entry": entry_net,
                        "qty": size / entry_net,
                        "sl": float(sig.stop_loss),
                        "tp": float(sig.take_profit),
                    }
                    cash -= size

        # ── equity (شامل PnL شناور) ──
        mark = pos["qty"] * float(c.close) if pos else 0.0
        equity = cash + mark
        peak = max(peak, equity)
        if peak > 0:
            max_dd = max(max_dd, (peak - equity) / peak * 100)
        curve.append({"time": t, "capital": round(equity, 2)})

    # پوزیشن باز در انتها: با close آخر بسته می‌شود
    if pos is not None:
        last = candles[-1]
        exit_net = float(last.close) * (1 - exit_adj)
        revenue = pos["qty"] * exit_net
        cost = pos["qty"] * pos["entry"]
        cash += revenue
        trades.append({
            "symbol": pos["symbol"], "side": "BUY",
            "entry_time": pos["time"],
            "exit_time": int(last.time),
            "entry_price": round(pos["entry"], 8), "exit_price": round(exit_net, 8),
            "quantity": pos["qty"], "pnl": round(revenue - cost, 4),
            "pnl_pct": round((revenue - cost) / cost * 100, 2) if cost > 0 else 0,
            "exit_reason": "end_of_data", "duration_candles": len(candles) - 1 - pos["idx"],
        })

    wins = [x for x in trades if x["pnl"] > 0]
    losses = [x for x in trades if x["pnl"] <= 0]
    gross_win = sum(x["pnl"] for x in wins)
    gross_loss = abs(sum(x["pnl"] for x in losses))
    final = cash
    n = len(trades)

    return {
        "initial_capital": initial_capital,
        "final_equity": round(final, 2),
        "total_pnl": round(final - initial_capital, 2),
        "total_pnl_pct": round((final - initial_capital) / initial_capital * 100, 2),
        "total_trades": n,
        "wins": len(wins),
        "losses": len(losses),
        "win_rate": round(len(wins) / n * 100, 1) if n else 0.0,
        "profit_factor": round(gross_win / gross_loss, 2) if gross_loss > 0 else (None if not gross_win else 999.0),
        "max_drawdown_pct": round(max_dd, 2),
        "avg_win_pct": round(sum(x["pnl_pct"] for x in wins) / len(wins), 2) if wins else 0.0,
        "avg_loss_pct": round(sum(x["pnl_pct"] for x in losses) / len(losses), 2) if losses else 0.0,
        "signals": signals,
        "candles_analyzed": len(candles),
        "equity_curve": curve,
        "trades": trades,
    }
