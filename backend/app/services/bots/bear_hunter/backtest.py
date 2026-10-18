"""Backtest engine for Cooperation Strategy."""
import pandas as pd
from decimal import Decimal
from .strategy import enrich_dataframe, find_entry_signal
from .rules import calculate_fees
from .config import BearHunterConfig


def run_backtest(csv_path: str, initial_capital: Decimal = Decimal("100000"), human_direction: str = "bearish") -> dict:
    df = pd.read_csv(csv_path)
    df = enrich_dataframe(df)

    config = BearHunterConfig()
    capital = initial_capital
    position = None
    trades = []
    equity_curve = []
    
    total_fees = Decimal("0")
    total_gross = Decimal("0")
    exit_counts = {"SL": 0, "TP": 0, "TIMEOUT": 0, "trailing": 0}

    for i in range(len(df)):
        row = df.iloc[i]
        current_close = float(row['close'])
        current_high = float(row['high'])
        current_low = float(row['low'])

        if position:
            position['bars_held'] += 1
            if position['direction'] == 'long' and current_high > position.get('peak', 0):
                position['peak'] = current_high
            elif position['direction'] == 'short' and current_low < position.get('trough', float('inf')):
                position['trough'] = current_low

            initial_sl = position['sl']
            if config.use_trailing:
                if position['direction'] == 'long':
                    trailing_sl = position['peak'] - position['atr'] * config.trailing_atr_mult
                    effective_sl = max(initial_sl, trailing_sl)
                else:
                    trailing_sl = position['trough'] + position['atr'] * config.trailing_atr_mult
                    effective_sl = min(initial_sl, trailing_sl)
            else:
                effective_sl = initial_sl

            exit_price = None
            exit_reason = None

            if position['direction'] == 'short':
                if current_high >= effective_sl:
                    exit_price = effective_sl
                    exit_reason = "trailing" if effective_sl < initial_sl - 1e-9 else "SL"
                elif current_low <= position['tp']:
                    exit_price, exit_reason = position['tp'], "TP"
            elif position['direction'] == 'long':
                if current_low <= effective_sl:
                    exit_price = effective_sl
                    exit_reason = "trailing" if effective_sl > initial_sl + 1e-9 else "SL"
                elif current_high >= position['tp']:
                    exit_price, exit_reason = position['tp'], "TP"

            if exit_price is None and position['bars_held'] >= 24:
                exit_price, exit_reason = current_close, "TIMEOUT"

            if exit_price is not None:
                entry = position['entry']
                size = position['size']
                size_float = float(size)
                
                if position['direction'] == 'short':
                    gross_pnl = (entry - exit_price) / entry * size_float
                else:
                    gross_pnl = (exit_price - entry) / entry * size_float
                    
                fees = calculate_fees(size, position['bars_held'], config)
                net_pnl = Decimal(str(gross_pnl)) - fees.total
                
                capital += net_pnl
                total_gross += Decimal(str(gross_pnl))
                total_fees += fees.total
                exit_counts[exit_reason] += 1

                trades.append({
                    "entry_time": int(position['entry_time']),
                    "exit_time": int(row['open_time']),
                    "direction": position['direction'],
                    "entry": round(float(entry), 2),
                    "exit": round(float(exit_price), 2),
                    "reason": exit_reason,
                    "gross": round(float(gross_pnl), 2),
                    "fees": round(float(fees.total), 2),
                    "pnl": round(float(net_pnl), 2),
                    "win": net_pnl > 0
                })
                position = None

        if not position:
            # Pass the HUMAN direction to the bot to find an entry
            signal = find_entry_signal(df, i, human_direction, config)
            if signal:
                size = capital * Decimal("0.15")
                if size > 100_000: size = Decimal("100000")
                
                position = {
                    "direction": signal['direction'],
                    "entry": current_close,
                    "sl": float(signal['sl']),
                    "tp": float(signal['tp']),
                    "atr": float(signal['atr']),
                    "peak": current_high,
                    "trough": current_low,
                    "size": size,
                    "bars_held": 0,
                    "entry_time": row['open_time'],
                }

        equity_curve.append({"time": int(row['open_time']), "equity": float(capital)})

    wins = [t for t in trades if t['win']]
    losses = [t for t in trades if not t['win']]

    return {
        "initial_capital": float(initial_capital),
        "final_capital": float(capital),
        "total_pnl": float(capital - initial_capital),
        "total_pnl_pct": float((capital / initial_capital - 1) * 100),
        "total_gross": float(total_gross),
        "total_fees": float(total_fees),
        "total_trades": len(trades),
        "wins": len(wins),
        "losses": len(losses),
        "exit_counts": exit_counts,
        "trades": trades,
        "equity_curve": equity_curve,
    }
