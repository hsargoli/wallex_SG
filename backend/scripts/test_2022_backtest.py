import sys
from pathlib import Path
from decimal import Decimal

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app.services.bots.bear_hunter.backtest import run_backtest

def main():
    csv_path = BASE_DIR / "data" / "candles" / "BTCUSDT_1h_historical.csv"
    if not csv_path.exists():
        print(f"❌ File not found: {csv_path}")
        return

    print("=" * 60)
    print("📉 2022 BEAR MARKET BACKTEST (Real BTCUSDT Data)")
    print("=" * 60)
    print(f"Data: {csv_path.name}")
    
    # We force human_direction="bearish" because 2022 was a massive downtrend
    res = run_backtest(
        csv_path=str(csv_path),
        initial_capital=Decimal("5000000"),
        human_direction="bearish"
    )

    print(f"\n💰 Capital: {res['initial_capital']:,.0f} TMN → {res['final_capital']:,.0f} TMN")
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
