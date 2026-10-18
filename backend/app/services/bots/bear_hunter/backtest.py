"""Backtest engine for bear_hunter with ATR-based levels + Trailing Stop."""
import pandas as pd
from decimal import Decimal
from .strategy import enrich_dataframe, check_short_signal
from .rules import calculate_fees
from .config import BearHunterConfig


def run_backtest(csv_path: str, initial_capital: Decimal = Decimal("100000")) -> dict:
    df = pd.read_csv(csv_path)
    df = enrich_dataframe(df)

    config = BearHunterConfig()
    capital = initial_capital
    position = None
    trades = []
    equity_curve = []

    for i in range(len(df)):
        row = df.iloc[i]
        current_close = float(row['close'])
        current_high = float(row['high'])
        current_low = float(row['low'])

        # ── Manage open position ──
        if position:
            position['bars_held'] += 1

            if current_low < position['lowest_low']:
                position['lowest_low'] = current_low

            initial_sl = position['sl']
            if config.use_trailing:
                trailing_sl = position['lowest_low'] + position['atr_abs'] * config.trailing_atr_mult
                effective_sl = min(initial_sl, trailing_sl)
            else:
                effective_sl = initial_sl

            exit_price = None
            exit_reason = None

            if current_high >= effective_sl:
                exit_price = effective_sl
                exit_reason = "trailing" if effective_sl < initial_sl - 1e-9 else "SL"
            elif current_low <= position['tp']:
                exit_price = position['tp']
                exit_reason = "TP"
            elif position['bars_held'] >= 24:
                exit_price = current_close
                exit_reason = "TIMEOUT"

            if exit_price is not None:
                entry = position['entry']
                size = position['size']
                size_float = float(size)
                gross_pnl = (entry - exit_price) / entry * size_float
                fees = calculate_fees(size, position['bars_held'], config)
                net_pnl = Decimal(str(gross_pnl)) - fees.total
                capital += net_pnl

                trades.append({
                    "entry_time": int(position['entry_time']),
                    "exit_time": int(row['open_time']),
                    "entry": round(float(entry), 2),
                    "exit": round(float(exit_price), 2),
                    "reason": exit_reason,
                    "pnl": round(float(net_pnl), 2),
                })
                position = None

        # ── Look for new entry ──
        if not position:
            signal = check_short_signal(df, i, config)
            if signal:
                size = capital * Decimal("0.15")
                if size > 100_000:
                    size = Decimal("100000")
                position = {
                    "entry": current_close,
                    "sl": float(signal['sl']),
                    "tp": float(signal['tp']),
                    "atr_abs": float(signal['atr_abs']),
                    "lowest_low": current_low,
                    "size": size,
                    "bars_held": 0,
                    "entry_time": row['open_time'],
                }

        equity_curve.append({"time": int(row['open_time']), "equity": float(capital)})

    return {
        "initial_capital": float(initial_capital),
        "final_capital": float(capital),
        "total_pnl": float(capital - initial_capital),
        "total_pnl_pct": float((capital / initial_capital - 1) * 100),
        "total_trades": len(trades),
        "wins": sum(1 for t in trades if t['pnl'] > 0),
        "losses": sum(1 for t in trades if t['pnl'] <= 0),
        "trades": trades,
        "equity_curve": equity_curve,
    }
