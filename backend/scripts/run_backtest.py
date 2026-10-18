import sys
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
from app.services.bots.bear_hunter.backtest import run_backtest

csv_path = BASE_DIR / "data" / "candles" / "BTCTMN_1h.csv"
res = run_backtest(str(csv_path))

print("\n═══ نتایج بک‌تست (تفکیک شده) ═══")
print(f"سرمایه اولیه: {res['initial_capital']:,.0f} تومان")
print(f"سرمایه نهایی: {res['final_capital']:,.0f} تومان")
print(f"سود/ضرر خالص (Net): {res['total_pnl']:,.0f} تومان ({res['total_pnl_pct']:.2f}%)")
print(f"سود/ضرر ناخالص (Gross): {res['total_gross']:,.0f} تومان")
print(f"مجموع کارمزدها: {res['total_fees']:,.0f} تومان")
print(f"تعداد تریدها: {res['total_trades']} (برد: {res['wins']} / باخت: {res['losses']})")
if res['wins'] > 0 or res['losses'] > 0:
    wr = res['wins'] / res['total_trades'] * 100
    print(f"نرخ برد: {wr:.1f}%")
    print(f"میانگین سود (Avg Win): {res['avg_win']:,.0f} تومان")
    print(f"میانگین ضرر (Avg Loss): {res['avg_loss']:,.0f} تومان")
print(f"دلیل خروج: {res['exit_counts']}")
