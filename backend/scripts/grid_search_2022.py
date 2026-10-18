import sys
from pathlib import Path
from decimal import Decimal
import itertools

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app.services.bots.bear_hunter.backtest import run_backtest
from app.services.bots.bear_hunter.config import BearHunterConfig
from dataclasses import replace

def run_grid_search():
    csv_path = BASE_DIR / "data" / "candles" / "historical" / "BTCUSDT_1h.csv"
    
    rsi_values = [70.0, 75.0, 80.0]
    trail_values = [3.0, 4.0, 5.0]
    timeout = 72
    
    results = []
    
    print(f"{'RSI':<5} | {'Trail':<6} | {'PnL%':<8} | {'Trades':<7} | {'WR%':<5} | {'AvgWin':<8} | {'AvgLoss':<8}")
    print("-" * 65)
    
    for rsi, trail in itertools.product(rsi_values, trail_values):
        config = replace(
            BearHunterConfig(),
            rsi_overbought=rsi,
            trailing_atr_mult=trail,
            max_hold_hours=timeout
        )
        
        res = run_backtest(
            csv_path=str(csv_path),
            initial_capital=Decimal("5000000"),
            human_direction="bearish",
            config=config,
            start_date="2022-01-01",
            end_date="2022-12-31"
        )
        
        if "error" in res: continue
        
        wr = (res['wins'] / res['total_trades'] * 100) if res['total_trades'] > 0 else 0
        print(f"{rsi:<5.1f} | {trail:<6.1f} | {res['total_pnl_pct']:>6.2f}% | {res['total_trades']:>7} | {wr:>5.1f} | {res['avg_win']:>8.0f} | {res['avg_loss']:>8.0f}")
        results.append((rsi, trail, res['total_pnl_pct']))
    
    if results:
        best = max(results, key=lambda x: x[2])
        print("-" * 65)
        print(f"🏆 BEST: RSI={best[0]}, Trail={best[1]}, PnL={best[2]:.2f}%")

if __name__ == "__main__":
    run_grid_search()
