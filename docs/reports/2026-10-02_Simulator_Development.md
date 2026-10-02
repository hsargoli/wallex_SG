# گزارش توسعه — شبیه‌ساز ربات‌های معاملاتی (Wallex)

**پروژه:** ROSHD_SARV Bot / Wallex Backend
**تاریخ گزارش:** ۱۴۰۵/۰۷/۱۰ — 2026-10-02
**توسعه‌دهنده:** حسین سرگلی
**وضعیت:** نسخه‌ی اولیه کامل و کامیت‌شده

---

## 🎯 هدف پروژه

ساخت یک **شبیه‌ساز تاریخی (Backtest)** برای ربات‌های معاملاتی موجود، که:

- روی داده‌ی واقعی صرافی والکس اجرا شود
- از تایم‌فریم‌های معتبر (1h و 1D) استفاده کند
- بایاس‌های رایج بک‌تست (Look-ahead, Fee, Position Sizing) را رفع کند
- نتایج قابل اتکا برای تصمیم‌گیری لایو تولید کند
- از طریق UI فارسی با تاریخ شمسی قابل استفاده باشد

---

## 📅 تایم‌لاین کارها

### ۱۴۰۵/۰۷/۰۹ — 2026-09-30 (روز اول)

**موضوع:** راه‌اندازی و رفع خطاها

- دیباگ خطای TypeError در Simulator
- افزودن پارامتر strategy به کلاس Simulator
- تشخیص اشتباه دامنه‌ی API (تصحیح api.wallex.com به api.wallex.ir)

### ۱۴۰۵/۰۷/۱۰ صبح — 2026-10-02 (صبح)

**موضوع:** اتصال به API واقعی والکس

- تست موفق API کندل‌ها: GET https://api.wallex.ir/v1/udf/history
- ساخت اسکنر اولیه‌ی رمزارزها
- شناسایی ساختار پاسخ: s, t[], o[], h[], l[], c[], v[]
- تشخیص عدم پشتیبانی درست از 15m، 5m، 30m، 4h در والکس

**کشف کلیدی:** والکس برای تایم‌فریم 1h فقط حدود ۷۲۰ کندل آخر (۳۰ روز) را نگه می‌دارد.

### ۱۴۰۵/۰۷/۱۰ بعد از ظهر — 2026-10-02 (بعد از ظهر)

**موضوع:** ساخت شبیه‌ساز چند‌رباتی

**بکاند:**
- ساخت app/services/bot_simulator.py با معماری Adapter
- Adapterها: TrendFollow, VolatilityHunter, MeanRevert
- بازنویسی WallexMarketData.get_candles() برای OHLCV کامل
- Endpointهای جدید: /bots, /symbols, /compare
- افزودن پارامتر initial_balance به endpointها

**فرانت:**
- افزودن dropdown رمزارز (BTC, ETH, BNB, SOL, XRP, ADA, DOGE)
- افزودن dropdown ربات با توضیحات و tags
- دکمه‌ی مقایسه با جدول مرتب‌شده (مدال)
- input سرمایه‌ی اولیه
- رفع خطای TypeScript در Alert

### رفع بایاس‌ها

**سه بایاس مهم که رفع شد:**

1. **Look-ahead Bias:**
   - قبل: تصمیم و ورود هر دو روی close[i]
   - بعد: تصمیم روی close[i], اجرا روی open[i+1]

2. **کارمزد معاملات:**
   - قبل: fee_pct نادیده گرفته می‌شد
   - بعد: از config ربات (۰.۲٪ در هر طرف)

3. **Position Sizing:**
   - قبل: ۱۰۰٪ سرمایه درگیر
   - بعد: از position_size_pct ربات (۳۰٪)

**نتیجه‌ی رفع بایاس (BTC، ۳۰ روز):**
- روندر: +3.64% (بایاس‌دار) به -1.03% (واقعی)
- نوسانگیر: 0% به +2.69%

---

## 🏗 معماری نهایی

Frontend (Next.js)
  Paper Trading Page: dropdowns (symbol, bot, range, balance)
       |
       v
FastAPI (simulation.py)
  /bots | /symbols | /run | /compare | /available-dates
       |
       v
BotSimulator (bot_simulator.py)
  - مدیریت pending orders (ورود/خروج در open کندل بعدی)
  - چک SL/TP با high/low کندل
  - کسر کارمزد و Position Sizing
  - بستن اجباری در پایان
       |
       v
WallexMarketData (wallex_repo.py)
  - get_candles(symbol, start, end, timeframe)
  - اتصال به https://api.wallex.ir/v1/udf/history

Adapters:
  TrendFollowAdapter    -> trend_follow/strategy.py
  VolatilityHunter      -> volatility_hunter/strategy.py
  MeanRevertAdapter     -> bounce_scalper + dispatcher

---

## 📊 نتایج تست‌ها (۳۰ روز / 1h — 2026-09-02 تا 2026-10-02)

### ETHUSDT

| رتبه | ربات | معاملات | نرخ برد | PnL |
|------|------|---------|---------|-----|
| 1 | نوسان‌گیر | 5 | 80% | +4.01% |
| 2 | کف‌زن | 13 | 38.5% | -0.74% |
| 3 | روندر | 14 | 21.4% | -1.81% |

### مشاهده‌ی کلی (۷ رمزارز)

- نوسان‌گیر: در ۶ از ۷ رمزارز مثبت — بهترین عملکرد کلی
- روندر: مناسب روند (SOL, XRP)، ضعیف در رنج (BTC, ETH)
- کف‌زن: ناسازگاری تایم‌فریم (15m طراحی شده، 1h اجرا) — با هشدار نمایش داده می‌شود

---

## 📁 فایل‌های تغییر یافته

### Backend

- app/domain/strategy.py — بازنویسی استراتژی EMA
- app/domain/repository.py — اینترفیس
- app/infrastructure/wallex_repo.py — اتصال به API واقعی + OHLCV
- app/services/bot_simulator.py — جدید — شبیه‌ساز ربات‌ها
- app/services/simulator_engine.py — رفع خطا و به‌روزرسانی
- app/services/bots/volatility_hunter/config.py — تنظیم پارامترها
- app/presentation/api/v1/simulation.py — endpointهای جدید

### Frontend

- app/paper-trading/page.tsx — UI کامل شبیه‌ساز
- lib/api.ts — توابع و تایپ‌های جدید
- components/ui/alert.tsx — جدید

---

## 🎓 درس‌های آموخته

1. بایاس‌های پنهان بک‌تست می‌توانند سود را ۱۰ برابر بزرگ‌تر نشان دهند
2. محدودیت API صرافی روی طراحی استراتژی تأثیر مستقیم دارد
3. معماری Adapter اضافه کردن ربات جدید را به حدود ۲۰ خط کاهش می‌دهد
4. صداقت با کاربر مهم‌تر از نمایش اعداد زیباست

---

## 📌 کامیت‌های مهم

| هش | پیام |
|----|------|
| c7c7917 | feat(simulator): add multi-bot multi-symbol backtesting |
| 344f5a0 | chore: remove accidental empty 'asyncio' file |

---

## 🎯 قدم‌های بعدی

### کوتاه‌مدت
1. نمایش لیست معاملات در UI
2. منحنی سرمایه (Equity Curve)
3. خروجی CSV از نتایج

### میان‌مدت
4. رفع ناسازگاری mean_revert با 1h
5. اضافه کردن grid_bot (نیاز به شبیه‌ساز چندپوزیشنی)
6. تنظیم پارامترهای استراتژی از UI

### بلندمدت
7. Paper Trading زنده
8. تست‌نت والکس و سپس لایو
9. کش دیتابیس برای کندل‌های تاریخی

---

## ⚠️ هشدارهای مهم

- نتایج تاریخی = پیش‌بینی آینده نیست
- والکس محدودیت داده دارد: 1h فقط حدود ۳۰ روز، 1D نامحدود
- هزینه‌های واقعی بیشتر است: Slippage، تأخیر شبکه
- تست لایو حتماً با سرمایه‌ی کم شروع شود

---

**پایان گزارش — نسخه ۱.۰**
