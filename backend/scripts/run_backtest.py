import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.services.bots.bear_hunter.backtest import run_backtest

csv = "backend/data/candles/BTCTMN_1h.csv"
print(f"Running backtest on {csv}...")
res = run_backtest(csv)

print("\n═══ نتایج بک‌تست ═══")
print(f"سرمایه اولیه: {res['initial_capital']:,.0f} تومان")
print(f"سرمایه نهایی: {res['final_capital']:,.0f} تومان")
print(f"سود/ضرر کل: {res['total_pnl']:,.0f} تومان ({res['total_pnl_pct']:.2f}%)")
print(f"تعداد تریدها: {res['total_trades']}")

if res['trades']:
    print("\n۵ ترید آخر:")
    for t in res['trades'][-5:]:
        print(f"  {t['reason']}: {t['pnl']:,.0f} تومان")
