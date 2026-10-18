import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app.services.bots.bear_hunter.backtest import run_backtest

csv_path = BASE_DIR / "data" / "candles" / "BTCTMN_1h.csv"
print(f"Running backtest on: {csv_path}")

res = run_backtest(str(csv_path))

print("\n═══ نتایج بک‌تست (ATR + Trailing + Volume) ═══")
print(f"سرمایه اولیه: {res['initial_capital']:,.0f} تومان")
print(f"سرمایه نهایی: {res['final_capital']:,.0f} تومان")
print(f"سود/ضرر کل: {res['total_pnl']:,.0f} تومان ({res['total_pnl_pct']:.2f}%)")
print(f"تعداد تریدها: {res['total_trades']} (برد: {res['wins']} / باخت: {res['losses']})")

if res['total_trades'] > 0:
    wr = res['wins'] / res['total_trades'] * 100
    print(f"نرخ برد (Win Rate): {wr:.1f}%")

if res['trades']:
    print("\n۵ ترید آخر:")
    for t in res['trades'][-5:]:
        print(f"  {t['reason']}: {t['pnl']:,.0f} تومان (entry={t['entry']:,.0f} → exit={t['exit']:,.0f})")
