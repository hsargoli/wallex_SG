# 🏗️ راهنمای پروژه والکس — برای AI

> این سند مخصوص پروژه **والکس** است.
> برای منش و قواعد عمومی، اول `~/Documents/AI_PRIMER.md` را بخوان.

---

## 🎯 این پروژه چیه؟

**Wallex Trading Platform** — پلتفرم معاملات الگوریتمی روی صرافی والکس (wallex.ir).

### قابلیت‌های اصلی
- ۸ ربات معاملاتی (trend_follow, scalp_master, mean_revert, ...)
- اسکنر بازار (تحلیل تکنیکال روی ۳۰۰+ نماد)
- سیگنال خرید/فروش با دلایل فارسی
- Paper Trading (شبیه‌سازی زنده)
- Live Order (LIMIT + STOP_LIMIT روی API واقعی والکس)
- مدیریت دارایی (portfolio + cost basis)
- چارت حرفه‌ای (TradingView-style)

### تکنولوژی
- **Backend:** FastAPI + Python 3.12 + uv
- **Frontend:** Next.js 16 + TypeScript + Tailwind v4 + shadcn/ui
- **Database:** فعلاً in-memory + CSV (SQLite/Postgres در برنامه)
- **معماری:** DDD + Hexagonal

### آمار فعلی (2026-10-09)
- ۱۰۰ تست پاس
- ۷۱+ endpoint
- ۱۹ صفحه فرانت
- ۸ ربات

---

## 📁 ساختار پوشه‌ها

~/wallex/
├── backend/
│ ├── app/
│ │ ├── domain/ ← قلب کسب‌وکار (بدون وابستگی)
│ │ │ ├── entities/ ← Candle, Market, Order, Balance
│ │ │ ├── ports/ ← قراردادها (ExchangePort)
│ │ │ ├── value_objects/ ← Symbol, OrderSide, OrderStatus
│ │ │ └── models/
│ │ ├── application/
│ │ │ └── use_cases/ ← GetCandlesUseCase, GetMarketsUseCase
│ │ ├── infrastructure/
│ │ │ ├── exchange/wallex/ ← WallexExchange + mapper
│ │ │ ├── paper_trading/
│ │ │ └── backtest/
│ │ ├── presentation/api/v1/ ← routers + schemas
│ │ ├── services/ ← bots, indicators, signal_engine, levels
│ │ └── core/ ← config, logging, rate_limit
│ ├── tests/
│ ├── scripts/ ← fetch_candles.py, tools/
│ └── data/candles/ ← CSV store
├── frontend/
│ ├── app/ ← صفحات Next.js
│ ├── components/ ← charts, dashboard, markets, signals, scanner
│ ├── lib/ ← api.ts, queries.ts, format.ts, hooks/
│ └── public/
├── docs/
│ ├── AI_PROJECT_GUIDE.md ← همین سند
│ ├── ARCHITECTURE.md
│ ├── API.md
│ ├── CONVENTIONS.md
│ ├── ROADMAP.md
│ ├── adr/ ← 0001..0006
│ ├── reports/ ← گزارش‌های روزانه
│ └── bots/ ← مستند هر ربات
└── scripts/verify.sh
text


---

## 🔒 قاعده‌ی طلایی — جهت وابستگی

**دومین قلب پروژه است. هیچ‌چیز به دومین وابسته نیست. همه‌چیز به دومین وابسته است.**

Presentation (FastAPI)
↓
Application (Use Cases)
↓
Domain (Entities, Ports)
↑
Infrastructure (Wallex, DB)
text


### ✅ درست

```python
# domain/entities/candle.py
from dataclasses import dataclass
from decimal import Decimal
# بدون import از FastAPI/Wallex/SQLAlchemy

@dataclass(frozen=True)
class Candle:
    time: int
    open: Decimal
    close: Decimal

python

# application/use_cases/get_candles.py
from app.domain.ports import ExchangePort
from app.domain.entities import Candle

class GetCandlesUseCase:
    def __init__(self, exchange: ExchangePort) -> None:
        self.exchange = exchange

python

# infrastructure/exchange/wallex/client.py
from app.domain.entities import Candle

class WallexExchange:  # پیاده‌سازی ExchangePort
    async def get_candles(self, symbol: str) -> list[Candle]: ...

❌ غلط
python

# ❌ domain به FastAPI وابسته شد
from fastapi import HTTPException

# ❌ application به Infrastructure وابسته شد
from app.infrastructure.exchange.wallex.client import WallexExchange

🎯 «کد جدید کجا بره؟» — چک‌لیست

۱. قاعده‌ی کسب‌وکار خالص؟ → domain/entities/ یا value_objects/
۲. سناریو؟ → application/use_cases/
۳. پیاده‌سازی خاص (Wallex/DB/file)؟ → infrastructure/
۴. endpoint جدید؟ → presentation/api/v1/{topic}.py + schemas.py + router.py
۵. ربات یا اندیکاتور؟ → services/bots/{name}/ یا services/indicators.py
۶. کمکی؟ → core/ یا services/
🧩 مثال: endpoint جدید

مرحله ۱ — Port لازمه؟ اگه داده‌ی جدید از صرافی → domain/ports/exchange.py
مرحله ۲ — Use Case لازمه؟ منطق پیچیده → application/use_cases/get_overview.py
مرحله ۳ — endpoint کجا؟ → presentation/api/v1/markets.py + schema
مرحله ۴ — تست: tests/test_overview.py
مرحله ۵ — شاهد: curl http://localhost:8000/v1/markets/overview/BTCTMN
🧩 مثال: ربات جدید

مرحله ۱ — mkdir backend/app/services/bots/my_bot/
مرحله ۲ — bot.py (BaseBot), config.py (dataclass), __init__.py
مرحله ۳ — ثبت در services/bots/registry.py
مرحله ۴ — تست: tests/test_my_bot.py
مرحله ۵ — مستند: docs/bots/my_bot.md (طبق الگوی trend_follow)
🔧 دستورات پرکاربرد
Backend
bash

cd ~/wallex/backend && source .venv/bin/activate
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
uv run pytest -q
uv add {package}
uv run python -m scripts.fetch_candles

Frontend
bash

cd ~/wallex/frontend
npm run dev
npx tsc --noEmit
npm run build

verify
bash

cd ~/wallex && bash scripts/verify.sh

📚 مستندات کلیدی
سند	چیه
~/Documents/AI_PRIMER.md	منش + قواعد عمومی (همه‌ی پروژه‌ها)
docs/AI_PROJECT_GUIDE.md	همین سند
docs/ARCHITECTURE.md	معماری کامل
docs/API.md	endpointها
docs/ROADMAP.md	نقشه‌ی راه ۶ فاز
docs/adr/	تصمیم‌های معماری (ADR)
docs/reports/	گزارش‌های روزانه
🎨 قواعد فرانت (اختصاصی والکس)

    کامپوننت reusable: props مثل compact, beginner, simple

    format: formatPrice (دقیق بدون K/M), formatPriceSmart (هوشمند)

    RTL: همه‌ی متن‌ها dir="rtl"

    InfoTip: برای توضیح مفاهیم فنی

    Anchor: پیوند بین خلاصه و جزئیات

    React Query: staleTime منطقی، query keys ثابت

🚨 قواعد خاص والکس

    ❌ git add -A نه — فایل خاص یا docs/

    Docker نیست — همه‌چیز لوکال

    DB: in-memory + CSV (data/candles/)

    cron: 30 3 * * * + @reboot (catch-up)

    LIVE_TRADING_ENABLED: true طبق ADR-0001

    API والکس: ۲۹ روز کندل ساعتی، ۴۰۰ روز روزانه

    ⚠️ از nohup برای backend استفاده نکن — با --reload کافیه

🤝 تیم

    حسین: رهبر محصول، تصمیم‌گیرنده نهایی

    دی: مشاور ارشد بکند، معماری، بازبینی

    مهر: مهندس فرانت‌اند

    نووآ: دستیار هوشمند، استانداردها

قاعده: پیشنهاد بده، تحمیل نکن. امضای نهایی با حسین.

جریان کاری:
۱. AI_PRIMER + این سند را بخوان
۲. git status و git log را چک کن
۳. با کاربر تأیید کن: کی هستم، کجا، اولین کار
۴. شاهد بگیر → تغییر → شاهد بعد
۵. commit atomic
۶. تصمیم مهم → ADR
🔄 جریان‌های اصلی

۱. قیمت: Wallex API → WallexExchange.get_markets() → mapper → Market entity → /v1/markets → useMarkets()

۲. کندل: Wallex API → get_candles() → mapper → Candle → /v1/markets/candles/{symbol} → useCandles() → ProChart

۳. سیگنال: Candle[] → signal_engine.generate_signal() → indicators + levels + rules → /v1/signals/{symbol} → SignalHero

۴. Paper Trading: PaperEngine (per bot) → fetch → signal → decision → PaperRepository → dashboard

۵. Order Chase: User → order_chase.worker → loop → Wallex LIMIT
🧪 تست

    هر endpoint جدید → ۱ تست

    هر Use Case → ۱ happy path

    هر ربات → ۱ تست logic (بدون I/O)

    قبل از commit → uv run pytest -q

🚀 آماده‌ای؟

    □

    ~/Documents/AI_PRIMER.md را خواندم
    □

    این سند را خواندم
    □

    git status --short را دیدم
    □

    git log --oneline -5 را دیدم
    □

    از کاربر پرسیدم: «من کی هستم؟ در چه پروژه‌ای؟ اولین کار چیه؟»
    □

    منتظر جواب کاربر ماندم

اگر همه ✅ — بریم! 🌿

«آهسته، مطمئن، با شاهد، با بازبینی، با مهربانی.»

آخرین آپدیت: 2026-10-09
نسخه: 1.0
