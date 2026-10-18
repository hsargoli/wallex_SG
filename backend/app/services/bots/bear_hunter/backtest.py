"""Backtest engine for bear_hunter."""
import pandas as pd
from decimal import Decimal
from .strategy import calculate_rsi, calculate_ema, calculate_adx, check_short_signal
from .rules import calculate_short_levels, calculate_short_net_pnl
from .config import BearHunterConfig

def run_backtest(csv_path: str, initial_capital: Decimal = Decimal("100000")) -> dict:
    df = pd.read_csv(csv_path)
    df['rsi'] = calculate_rsi(df['close'])
    df['ema'] = calculate_ema(df['close'])
    df['adx'] = calculate_adx(df['high'], df['low'], df['close'])
    
    config = BearHunterConfig()
    capital = initial_capital
    position = None
    trades = []
    equity_curve = []
    
    for i in range(len(df)):
        current_close = Decimal(str(df['close'].iloc[i]))
        current_time = df['open_time'].iloc[i]
        
        if position:
            position['bars_held'] += 1
            sl_hit = False
            tp_hit = False
            
            high = Decimal(str(df['high'].iloc[i]))
            low = Decimal(str(df['low'].iloc[i]))
            
            if high >= position['sl']: sl_hit = True
            elif low <= position['tp']: tp_hit = True
                
            exit_reason = None
            exit_price = None
            
            if sl_hit:
                exit_price = position['sl']
                exit_reason = "SL"
            elif tp_hit:
                exit_price = position['tp']
                exit_reason = "TP"
            elif position['bars_held'] >= 24:
                exit_price = current_close
                exit_reason = "TIMEOUT"
                
            if exit_price:
                pnl_obj = calculate_short_net_pnl(
                    entry_price=position['entry'], exit_price=exit_price,
                    position_size_tmn=position['size'], hours_held=position['bars_held'],
                    capital_tmn=capital, config=config
                )
                capital += pnl_obj.net_pnl
                trades.append({
                    "entry_time": position['entry_time'], "exit_time": current_time,
                    "entry": float(position['entry']), "exit": float(exit_price),
                    "reason": exit_reason, "pnl": float(pnl_obj.net_pnl)
                })
                position = None
                
        if not position:
            if check_short_signal(df, i):
                size = capital * Decimal("0.15")
                if size > 100_000: size = Decimal("100000")
                levels = calculate_short_levels(current_close, config)
                position = {
                    "entry": current_close, "sl": levels.stop_loss, "tp": levels.take_profit,
                    "size": size, "bars_held": 0, "entry_time": current_time
                }
                
        equity_curve.append({"time": current_time, "equity": float(capital)})
        
    return {
        "initial_capital": float(initial_capital), "final_capital": float(capital),
        "total_pnl": float(capital - initial_capital), "total_pnl_pct": float((capital / initial_capital - 1) * 100),
        "total_trades": len(trades), "trades": trades, "equity_curve": equity_curve
    }
