تیم: ROSHD_SARV
سرمایه هدف: ۳۰۰٬۰۰۰ تومان (اولیه)
وضعیت: ۵ ربات ساخته شده، آماده برای Paper Trading
🏗️ ساختار کلی پروژه
text

~/wallex/
├── backend/                    ← FastAPI + Python 3.12
│   ├── app/
│   │   ├── main.py            ← Application Factory
│   │   ├── core/              ← config, logging, exceptions
│   │   ├── domain/            ← Entities, Ports, Value Objects
│   │   ├── application/       ← Use Cases
│   │   ├── infrastructure/    ← Wallex adapter
│   │   ├── presentation/      ← API routers
│   │   └── services/          ← Business logic
│   │       ├── indicators.py
│   │       ├── bottom_detector.py
│   │       ├── regime_detector.py
│   │       ├── signal_engine.py
│   │       ├── levels.py
│   │       ├── trend.py
│   │       ├── ml_bottom_model.py
│   │       ├── anomaly_detector.py
│   │       ├── volatility_predictor.py
│   │       ├── paper_trader.py
│   │       ├── paper_trader_v2.py
│   │       ├── historical_replay.py
│   │       ├── budget_service.py
│   │       ├── smart_dispatcher.py
│   │       └── bots/          ← 🆕 معماری ربات‌ها
│   │           ├── base.py
│   │           ├── registry.py
│   │           ├── mean_revert/
│   │           ├── trend_follow/
│   │           ├── grid_bot/
│   │           ├── volatility_hunter/
│   │           └── smart_portfolio/
│   │
│   ├── scripts/ml/            ← اسکریپت‌های تحلیل
│   ├── tests/                 ← ۷۶ تست
│   ├── data/                  ← SQLite, models, state
│   └── .venv/
│
├── frontend/                  ← Next.js 16 + Tailwind v4
│   ├── app/
│   │   ├── layout.tsx         ← RTL + Vazirmatn
│   │   ├── page.tsx           ← Dashboard
│   │   ├── bots/              ← 🆕 لیست و جزئیات ربات‌ها
│   │   ├── portfolio/         ← سبد دارایی
│   │   ├── wallet/            ← کیف پول
│   │   ├── markets/           ← بازارها + چارت
│   │   ├── signals/           ← سیگنال‌ها
│   │   ├── scanner/           ← اسکنر بازار
│   │   └── paper-trading/     ← Paper Trading
│   ├── components/
│   │   ├── layout/sidebar.tsx
│   │   ├── ui/                ← shadcn components
│   │   ├── portfolio/
│   │   ├── signals/
│   │   ├── markets/
│   │   └── charts/
│   ├── lib/
│   │   ├── api.ts             ← API client
│   │   ├── queries.ts         ← React Query hooks
│   │   ├── format.ts
│   │   └── utils.ts
│   └── package.json
│
└── docs/
    ├── README.md
    └── reports/
        ├── 2026-09-30.md
        ├── 2026-09-30_ML_Experiments.md
        └── ML_JOURNEY.md

🚀 مسیر طی‌شده (Timeline)
📌 Milestone 1-4: زیرساخت (قبلاً)
text

✅ راه‌اندازی FastAPI
✅ اتصال به والکس (API client)
✅ مپ کردن داده‌ها (mapper)
✅ endpoint موجودی (key-assets)
✅ Budget Manager (مدیریت بودجه)

📌 Milestone 5: Market Data Layer
text

✅ دریافت Order Book
✅ محاسبه best_bid, best_ask, spread
✅ Candlestick data (15m, 1h, 4h, 1D)
✅ Candle aggregator (ادغام 1m → 15m)
✅ Depth chart در فرانت

📌 Milestone 6: Profitability Checker
text

✅ محاسبه سود با کارمزد
✅ پشتیبانی Maker/Taker
✅ Slippage calculation
✅ min_profitable_spread
✅ is_profitable flag

📌 Indicator & Signal Engine
text

✅ RSI, EMA, MACD, Bollinger, ATR
✅ ۶ قانون سیگنال (rules-based)
✅ Pivot Points + S/R Levels
✅ Signal history
✅ Multi-timeframe analysis

📌 ML Experiments (پروژه موقت)
text

❌ RandomForest, LightGBM, XGBoost
❌ AUC بین 0.31-0.72 (overfitting شدید)
❌ در-sample 0.96 / out-sample 0.52
📝 نتیجه: داده کافی نیست (فقط 20 روز)

درس مهم: ML در ترید بدون داده کافی شکست می‌خوره

📌 Paper Trading
text

✅ PaperTrader (نسخه ۱)
✅ PaperTraderV2 (با Smart Dispatcher)
✅ HistoricalReplayBot (تست روی گذشته)
✅ ذخیره‌سازی state
✅ Equity curve tracking

📌 Scanner & Per-Asset Analysis
text

✅ اسکن ۱۸۷ مارکت با صفحه‌بندی
✅ مرتب‌سازی بر اساس حجم
✅ Trend score هر نماد
✅ تشخیص استراتژی مناسب هر نماد

📌 ۵ ربات معاملاتی 🆕
🥇 کف‌زن (Mean Revert Bot)
text

slug: mean_revert | v0.1.0
استراتژی: کف می‌خره، سود کوچک
R/DD: 2.38
بازده: +8.1%  |  DD: 3.4%

🥈 روندرو (Trend Follow Bot)
text

slug: trend_follow | v0.1.0
استراتژی: EMA Cross + ADX + Trailing Stop
R/DD: 2.41
بازده: +6.8%  |  DD: 2.8%

🥉 نوسان‌گیر (Volatility Hunter Bot) 🏆
text

slug: volatility_hunter | v0.1.0
استراتژی: تشخیص range + خرید کف + فروش سقف
R/DD: 6.25 (بهترین!)
بازده: +31.85%  |  DD: 5.1%

📊 شبکه‌ای (Grid Bot)
text

slug: grid_bot | v0.1.0
استراتژی: پله‌ای خرید/فروش در محدوده
R/DD: 1.00
بازده: +8.9%  |  DD: 8.9%

🧠 پورتفوی هوشمند (Smart Portfolio)
text

slug: smart_portfolio | v0.1.0
نقش: مسیریابی بین ۴ ربات بر اساس رژیم
نقشه: trending_up → روندرو
      ranging → کف‌زن + شبکه‌ای
      choppy → نوسان‌گیر
      trending_down → هیچکس

🔬 ابزارهای تحلیلی ساخته‌شده
۱. Indicator Engine
text

SMA, EMA, RSI, MACD, Bollinger Bands, ATR

۲. Regime Detector
text

معیارها:
  • ADX (قدرت روند)
  • ATR% (نوسان)
  • EMA Alignment (جهت)

رژیم‌ها:
  • trending_up
  • trending_down
  • ranging
  • choppy

۳. Bottom Detector
text

۵ نشانه‌ی کف:
  • RSI oversold
  • RSI divergence
  • Volume spike
  • Rejection wick
  • Support touch

۴. Smart Dispatcher
text

انتخاب استراتژی مناسب هر نماد
(از پیکربندی JSON)

۵. Anomaly Detector
text

Isolation Forest
تشخیص وضعیت غیرعادی بازار

۶. Volatility Predictor
text

Gradient Boosting
پیش‌بینی نوسان آینده

🎨 فرانت‌اند (Next.js 16)
صفحات ساخته‌شده
text

/dashboard        ← نمای کلی
/wallet           ← کیف پول والکس (۹.۳M تومان)
/portfolio        ← سبد دارایی با toggle bid/last
/markets          ← لیست ۳۷۳ بازار
/markets/[symbol] ← Order Book + Depth Chart
/markets/[symbol]/chart ← چارت کندل استیک
/signals/[symbol] ← تحلیل کامل نماد
/scanner          ← اسکنر با صفحه‌بندی
/paper-trading    ← Paper Trading live
/bots             ← 🆕 لیست ۵ ربات
/bots/[slug]      ← جزئیات ربات با کنترل
/budget           ← مدیریت بودجه
/profitability    ← محاسبه سود

ویژگی‌های UI
text

✅ RTL کامل + فونت Vazirmatn
✅ Dark theme تریدینگ
✅ React Query با auto-refetch
✅ Sidebar با وضعیت live API
✅ Equity charts
✅ Order Book table
✅ Candlestick chart (TradingView style)

📊 آمار نهایی
متریک	مقدار
فایل‌های Python	~۸۰
تست‌ها	۷۶ (۱۰۰٪ پاس)
Ruff	✅ All checks passed
فایل‌های TypeScript	~۵۰
صفحات Next.js	۱۲
کامپوننت‌های React	۱۵
TypeScript errors	۰
ربات‌ها	۵
اسکریپت‌های ML	۲۵+
خطوط کد کل	~۱۵,۰۰۰
💡 درس‌های کلیدی
۱. ML در ترید
text

❌ ML بدون داده کافی = شکست
❌ Overfitting شدید حتی با ۸ مدل مختلف
✅ ML به عنوان کمک‌کننده، نه تصمیم‌گیرنده

۲. Backtest و Reality
text

⚠️ نتایج "too good to be true" = باگ
⚠️ حتماً حساب‌داری رو چک کن
⚠️ per-symbol analysis ضروریه

۳. Architecture
text

✅ BaseBot + Registry
✅ Per-asset strategy
✅ Regime-based routing
✅ Paper-first approach

۴. Perception تیم
text

این پروژه ۳ روزه ساخته شد:
  • روز ۱: زیرساخت + ML experiments
  • روز ۲: Candles + Charts + Signals
  • روز ۳: ۵ ربات + Smart Portfolio

🎯 مسیر ادامه
کوتاه‌مدت
text

🔄 تست کامل Smart Portfolio
🔄 Paper Trading با ۵ ربات
🔄 Live Execution Engine (dry-run)

میان‌مدت
text

🔜 Live با ۱۰۰K تومان
🔜 جمع‌آوری داده (۶ ماه)
🔜 ML با داده کافی

بلندمدت
text

🔮 ربات‌های بیشتر
🔮 Pairs Trading
🔮 Volume Profile
🔮 مقیاس‌بندی سرمایه

🏆 دستاوردهای اصلی
text

✅ معماری حرفه‌ای (DDD + Clean)
✅ ۵ ربات متنوع
✅ Smart Portfolio (رویکرد کوانت واقعی)
✅ بهترین ربات: نوسان‌گیر (R/DD 6.25)
✅ فرانت کامل با ۱۲ صفحه
✅ ۷۶ تست پاس
✅ مستندات کامل

آخرین Commit:
text

feat(volatility-hunter): wide test + reality check (R/DD 6.25)
