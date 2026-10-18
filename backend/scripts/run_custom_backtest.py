import sys
import argparse
from pathlib import Path
from decimal import Decimal

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app.services.bots.bear_hunter.backtest import run_backtest
from app.services.bots.bear_hunter.config import BearHunterConfig

def main():
    parser = argparse.ArgumentParser(description="Custom Backtest Runner")
    parser.add_argument("--symbol", type=str, default="BTCUSDT", help="BTCUSDT, ETHUSDT, SOLUSDT")
    parser.add_argument("--start", type=str, required=True, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", type=str, required=True, help="End date (YYYY-MM-DD)")
    parser.add_argument("--direction", type=str, default="bearish", choices=["bearish", "bullish"])
    parser.add_argument("--rsi", type=float, default=70.0, help="RSI threshold")
    parser.add_argument("--trail", type=float, default=3.0, help="Trailing ATR multiplier")
    parser.add_argument("--timeout", type=int, default=24, help="Max hold hours")
    
    args = parser.parse_args()
    
    csv_path = BASE_DIR / "data" / "candles" / "historical" / f"{args.symbol}_1h.csv"
    if not csv_path.exists():
        print(f"❌ File not found: {csv_path}")
        return

    print("=" * 60)
    print(f"📊 BACKTEST: {args.symbol} | {args.start} to {args.end}")
    print(f"⚙️  Direction: {args.direction} | RSI: {args.rsi} | Trail: {args.trail}")
    print("=" * 60)

    from dataclasses import replace
    config = replace(
        BearHunterConfig(),
        rsi_overbought=args.rsi,
        trailing_atr_mult=args.trail,
        max_hold_hours=args.timeout
    )

    res = run_backtest(
        csv_path=str(csv_path),
        initial_capital=Decimal("5000000"),
        human_direction=args.direction,
        config=config,
        start_date=args.start,
        end_date=args.end
    )

    if "error" in res:
        print(f"❌ {res['error']}")
        return

    print(f"💰 Capital: {res['initial_capital']:,.0f} TMN → {res['final_capital']:,.0f} TMN")
    print(f"📈 Net PnL: {res['total_pnl']:,.0f} TMN ({res['total_pnl_pct']:.2f}%)")
    print(f"📊 Trades: {res['total_trades']} (Wins: {res['wins']} / Losses: {res['losses']})")
    
    if res['total_trades'] > 0:
        win_rate = (res['wins'] / res['total_trades']) * 100
        print(f"🎯 Win Rate: {win_rate:.1f}%")
        print(f"   Avg Win: {res['avg_win']:,.0f} TMN")
        print(f"   Avg Loss: {res['avg_loss']:,.0f} TMN")
    
    print(f"🚪 Exit Reasons: {res['exit_counts']}")
    print("=" * 60)

if __name__ == "__main__":
    main()
