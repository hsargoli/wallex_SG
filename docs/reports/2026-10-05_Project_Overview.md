# دید کلی پروژه والکس

**تاریخ (میلادی):** 2026-10-05
**تاریخ (شمسی):** 1405/07/15
**وضعیت:** فعال — در حال توسعه

---

## 🎯 معرفی کلی

**پلتفرم معاملاتی والکس** — یک سیستم کامل برای معامله‌ی رمزارزها در صرافی والکس ایران.

### برای کیه؟
- **تریدر تازه‌کار:** صفحات ساده + آموزش + راهنما
- **تریدر حرفه‌ای:** ابزارهای تحلیل عمیق + چارت حرفه‌ای + API

### فلسفه‌ی طراحی
- DDD (Domain-Driven Design) در Backend
- Component-based در Frontend
- تفکیک مسیر کاربر (تازه‌کار / حرفه‌ای)

---

## 🏗 معماری Backend

**Stack:** Python 3.12 + FastAPI + uv

### لایه‌ها (DDD)

backend/app/
├── domain/ ← Entities, Ports
│ ├── entities/ (Candle, Market, Order, ...)
│ └── ports/ (ExchangePort, ...)
│
├── application/ ← Use Cases
│ └── use_cases/
│ ├── get_candles.py
│ ├── get_candles_with_fallback.py
│ └── ...
│
├── infrastructure/ ← External adapters
│ └── exchange/wallex/ (Client, Mapper)
│
├── presentation/ ← API endpoints
│ └── api/v1/
│ ├── account.py
│ ├── bots.py
│ ├── markets.py
│ ├── orders.py
│ ├── scanner.py
│ ├── signals.py
│ └── ... (15 فایل)
│
├── services/ ← Business logic
│ ├── indicators.py (EMA, RSI, MACD, BB, ATR, ...)
│ ├── trend.py (analyze_trend)
│ ├── facts.py (تحلیل خودکار ۴-دوره)
│ ├── signal_engine.py
│ ├── bots/ (6 ربات)
│ ├── ml_bottom_model.py
│ └── ...
│
└── core/ ← Config
text


### API Endpoints (۵۵ تا)

| فایل | تعداد | موضوع |
|------|-------|-------|
| `account.py` | ۳ | موجودی، دارایی‌ها |
| `bots.py` | ۱۰ | مدیریت ربات‌ها |
| `bot.py` | ۲ | وضعیت ربات |
| `markets.py` | ۶ | بازارها، کندل، سطوح، فکت‌ها |
| `orders.py` | ۴ | سفارش‌ها |
| `signals.py` | ۵ | سیگنال‌ها |
| `scanner.py` | ۲ | اسکنر بازار |
| `paper_trading.py` | ۵ | Paper Trading v1 |
| `paper_v2.py` | ۴ | Paper Trading v2 |
| `replay.py` | ۴ | Replay تاریخی |
| `simulation.py` | ۵ | شبیه‌سازی |
| `profitability.py` | ۲ | محاسبه سود |
| `backtest.py` | ۱ | بک‌تست |
| `ml_bottom.py` | ۱ | ML Bottom Detection |
| `scalping.py` | ۱ | Scalping |

---

## 🎨 معماری Frontend

**Stack:** Next.js 16 + TypeScript + Tailwind v4 + shadcn/ui

### ساختار

frontend/
├── app/ ← Pages (16 صفحه)
│ ├── page.tsx ← داشبورد
│ ├── portfolio/ ← سبد دارایی
│ ├── bot-wallet/ ← کیف پول ربات
│ ├── markets/ ← بازارها
│ ├── markets/[symbol]/ ← جزئیات نماد (tabs)
│ ├── markets/[symbol]/chart/ ← چارت حرفه‌ای
│ ├── signals/ ← سیگنال‌ها
│ ├── signals/[symbol]/ ← جزئیات سیگنال (تازه‌کار)
│ ├── scanner/ ← اسکنر بازار
│ ├── bots/ ← ربات‌ها
│ ├── bots/[slug]/ ← جزئیات ربات
│ ├── orders/ ← سفارش‌ها
│ ├── order-bot/ ← ثبت سفارش دستی
│ ├── paper-trading/ ← Paper Trading
│ ├── profitability/ ← محاسبه سود
│ └── wallet/ ← redirect
│
├── components/ ← 67 کامپوننت
│ ├── charts/ ← ProChart, FactsCard, ChartLegend, ...
│ ├── dashboard/ ← KpiCards, ActionBar, ...
│ ├── markets/ ← MarketRow, MarketCard, ...
│ ├── signals/ ← SignalRow, SignalsChart, ...
│ ├── scanner/ ← ScannerTable, ScannerFilters, ...
│ ├── ui/ ← shadcn components
│ └── layout/ ← Sidebar, ThemeSwitcher
│
└── lib/ ← API + hooks
├── api.ts ← API client
├── queries.ts ← React Query hooks
├── format.ts
└── hooks/ ← Custom hooks
text


### صفحات کلیدی

| صفحه | برای کی | ویژگی |
|------|--------|-------|
| `/` | همه | داشبورد + ActionBar (CTA) |
| `/signals` | تازه‌کار | لیست سیگنال‌ها + راهنما |
| `/signals/[symbol]` | تازه‌کار | تحلیل ساده + آموزش |
| `/markets/[symbol]` | حرفه‌ای | Tabs: [تحلیل] [معامله] |
| `/markets/[symbol]/chart` | حرفه‌ای | چارت + RSI + MACD + فکت‌ها |
| `/scanner` | حرفه‌ای | فیلتر پیشرفته + multi-TF |

---

## 🤖 ربات‌ها

| ربات | استراتژی | فایل |
|------|----------|------|
| `mean_revert` | بازگشت به میانگین | `services/bots/mean_revert/` |
| `trend_follow` | پیروی از روند (EMA + ADX) | `services/bots/trend_follow/` |
| `grid_bot` | Grid Trading | `services/bots/grid_bot/` |
| `volatility_hunter` | شکار نوسان | `services/bots/volatility_hunter/` |
| `volatility_hunter_v2` | نسخه v2 با ADX + RSI | `services/bots/volatility_hunter_v2/` |
| `smart_portfolio` | تخصیص هوشمند | `services/bots/smart_portfolio/` |

**Registry:** `services/bots/registry.py`

---

## 🧠 زیرساخت ML

- **مدل:** `backend/data/models/bottom_model_v1.joblib` (1.3 MB)
- **کاربرد:** تشخیص کف قیمت
- **سرویس:** `services/ml_bottom_model.py`
- **Endpoint:** `/v1/ml-bottom/{symbol}`

---

## 🧪 تست‌ها

backend/tests/
├── contract/ ← API contract tests
├── integration/ ← End-to-end tests
└── unit/ ← Unit tests
text


**۷ فایل تست**

---

## 📚 مستندات

docs/
├── ARCHITECTURE.md ← معماری کلان
├── API.md ← مستندات endpoints
├── BOTS.md ← راهنمای ربات‌ها
├── ML_JOURNEY.md ← تاریخچه ML
├── SETUP.md ← راه‌اندازی
├── README.md ← نقشه
└── reports/ ← ۱۵ گزارش
├── 2026-09-30.md
├── 2026-10-02_Project_Audit.md
├── 2026-10-04_Stop_Price_Fix.md
├── 2026-10-05_Scanner_Rebuild.md
├── 2026-10-05_Chart_Pro_and_Fallback.md
├── 2026-10-05_Beginner_vs_Pro_Split.md
└── ...
text


---

## 📊 آمار کلی

| معیار | مقدار |
|-------|-------|
| Backend endpoints | ۵۵ |
| Frontend pages | ۱۶ |
| Frontend components | ۶۷ |
| خطوط کد Backend | ~۱۳,۱۴۳ |
| خطوط کد Frontend | ~۱۶,۶۴۳ |
| **کل خطوط کد** | **~۳۰,۰۰۰** |
| ربات‌ها | ۶ |
| مدل‌های ML | ۱ |
| گزارش‌ها | ۱۵ |

---

## 🎯 وضعیت فعلی

### ✅ کامل
- سفارش‌گذاری (LIMIT + STOP_LIMIT)
- ۶ ربات معاملاتی
- Paper Trading (v1 + v2)
- سیگنال‌ها + اسکنر
- چارت حرفه‌ای (RSI + MACD + Pivot + فکت‌ها)
- Analytics: FactsService (۴-دوره)
- داشبورد + ActionBar
- سایدبار گروه‌بندی‌شده
- تفکیک تازه‌کار / حرفه‌ای

### 🟡 نیمه‌کاره
- Live Trading Engine (ربات خودش تصمیم بگیره)
- `/profitability` (نیمه‌کاره)
- Drawing Tools روی چارت

### ❌ باقی‌مونده
- WebSocket برای قیمت زنده
- Postgres برای persistence
- Alerts / هشدار قیمت
- Replay Mode
- Onboarding / Help Center
- تست‌های Frontend

---

## 🚀 قدم‌های بعدی (پیشنهاد)

### کوتاه‌مدت
1. Drawing Tools (خط افقی، روند)
2. Alerts (هشدار قیمت)
3. Help Center + واژه‌نامه

### میان‌مدت
4. Replay Mode (بک‌تست بصری)
5. Postgres (persistence)
6. WebSocket (real-time)

### بلندمدت
7. Live Trading Engine
8. Multi-Chart Layout
9. Deployment به production

---

## 🏷 کامیت‌های کلیدی

7f44950 chore: final cleanup + extend .bak pattern
1278f23 chore: archive old .bak files
f3c8573 feat(chart): auto-generated facts + summary
6664ef2 feat(chart): resizable panes + synthetic candles
f8b0ae4 feat(markets): candles-v2 endpoint
90747e1 feat(signals): action-oriented KPIs
0372f56 feat(ui): regrouped sidebar + action dashboard
fec304e docs(reports): beginner vs pro split
text


**تگ‌ها:**
- `v1.0` — نسخه‌ی اولیه
- `checkpoint-before-scanner-rebuild` — نقطه‌ی برگشت

---

## 🎨 ویژگی‌های خاص

### ۱. Fallback از TF بالاتر
- والکس فقط ۳ TF واقعی داره: `1m`, `1h`, `1D`
- برای بازه‌های قدیمی، از `1D` شبیه‌سازی می‌کنیم
- کندل‌های شبیه‌سازی با رنگ آبی مشخص می‌شن

### ۲. FactsService (تحلیل ۴-دوره)
- ۱ سال (1D) + ۱ ماه (1h) + ۷ روز (1h) + ۸ ساعت (15m)
- محاسبه‌ی خودکار:
  * بازدهی، سقف/کف، نوسان (کندل + روزانه)
  * پولبک، نوسان‌های بزرگ با تاریخ
  * روند، هم‌راستایی دوره‌ها
- تفسیر متنی + توصیه

### ۳. تفکیک Beginner / Pro
- **`/signals/[symbol]`:** ساده، آموزشی
- **`/markets/[symbol]`:** حرفه‌ای، tabbed

### ۴. UI مدرن
- Dark theme + 5 رنگ
- RTL کامل
- Popover tooltips
- Progressive disclosure

---

## 🎯 نتیجه‌گیری

پروژه‌ی **والکس** یک پلتفرم معاملاتی **کامل و حرفه‌ای** است:
- **۵۵ endpoint** برای همه‌ی نیازها
- **۱۶ صفحه‌ی کاربری**
- **۶ ربات معاملاتی**
- **~۳۰,۰۰۰ خط کد**
- **۱۵ گزارش مستند**

**نقاط قوت:**
- معماری تمیز (DDD)
- تفکیک مسیر کاربر
- مستندسازی عالی
- UI/UX حرفه‌ای

**نقاط قابل بهبود:**
- تست‌های Frontend
- Real-time (WebSocket)
- Persistence (Postgres)

---

**پایان گزارش**
