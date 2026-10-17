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

---

## 🚀 Deploy & Server

**سرور:** `87.248.152.239` | SSH port `9011` | alias: `ssh myserver`

**مسیر پروژه:** `/home/deploy/wallex/`

### سرویس‌های systemd

| سرویس | پورت | مسیر |
|-------|------|------|
| `wallex-backend` | 127.0.0.1:8020 | `/home/deploy/wallex/backend/` |
| `wallex-frontend` | 0.0.0.0:3020 | `/home/deploy/wallex/frontend/` |
| `nginx` | :80 | — |

### .env سرور

- **مسیر:** `/home/deploy/wallex/.env` (والد `backend/`، نه داخلش)
- **owner:** `deploy:deploy`, `chmod 600`
- **systemd:** `EnvironmentFile=/home/deploy/wallex/.env`
- **alembic:** `env.py` از `(ROOT/.env, ROOT.parent/.env)` لود می‌کنه

~~~bash
# شاهد
sudo -u deploy grep -E "^(DATABASE_URL|JWT_SECRET_KEY)=" /home/deploy/wallex/.env | sed 's/=.*/=***/'
~~~

### الگوی deploy (Backend)

~~~bash
# 1. commit + push لوکال
git add <file>
git commit -m "..."
git push origin refactor/full-ddd

# 2. dry-run (اجباری — M22)
rsync -avzn --delete \
  --exclude='.venv' --exclude='__pycache__' --exclude='*.pyc' \
  --exclude='.env' --exclude='.git' \
  --exclude='data/candles' --exclude='data/guests' \
  --exclude='data/paper_v3' --exclude='data/paper_v2' \
  --exclude='data/paper_trading' --exclude='data/replay' \
  --exclude='data/nooaah' --exclude='data/models' \
  --exclude='data/backtest_results' --exclude='data/full_scan' \
  --exclude='data/api_limits' \
  -e "ssh -p 9011" \
  backend/ root@87.248.152.239:/home/deploy/wallex/backend/

# 3. rsync واقعی (بدون -n)

# 4. chown قبل از migration (اجباری)
ssh -p 9011 root@87.248.152.239 "chown -R deploy:deploy /home/deploy/wallex/backend"

# 5. migration (اگه schema عوض شده)
ssh -p 9011 root@87.248.152.239 << 'REMOTE'
sudo -u deploy bash -c '
  cd /home/deploy/wallex/backend
  .venv/bin/alembic current
  .venv/bin/alembic upgrade head
  .venv/bin/alembic current
'
REMOTE

# 6. restart backend
ssh -p 9011 root@87.248.152.239 "systemctl restart wallex-backend"
~~~

### الگوی deploy (Frontend)

~~~bash
# 1. dry-run
rsync -avzn --delete \
  --exclude='node_modules' --exclude='.next' \
  --exclude='.env.local' --exclude='.env' \
  --exclude='.git' --exclude='tsconfig.tsbuildinfo' \
  -e "ssh -p 9011" \
  frontend/ root@87.248.152.239:/home/deploy/wallex/frontend/

# 2. rsync واقعی

# 3. chown + build + restart
ssh -p 9011 root@87.248.152.239 << 'REMOTE'
chown -R deploy:deploy /home/deploy/wallex/frontend
su - deploy -c "cd /home/deploy/wallex/frontend && npm run build"
systemctl restart wallex-frontend
REMOTE
~~~

### nginx — public vs protected

**فایل:** `/etc/nginx/sites-available/wallex`

**Public (بدون Basic Auth):**
- `/api/backend/v1/markets/*`
- `/api/backend/v1/signals/*`
- `/api/backend/v1/scanner/*`
- `/api/backend/v1/analysis/*`
- `/api/backend/v1/auth/*` — JWT داخلی
- `/api/backend/v1/user/*` — JWT داخلی (فاز ۱۷.۷.۲)
- `/api/backend/v1/guest/*` — guest-token

**Protected (Basic Auth):**
- `/dashboard` و `/app/*`
- `/api/backend/v1/account/*`
- `/api/backend/v1/orders/*`

**الگوی بلوک public:**

~~~nginx
location /api/backend/v1/user/ {
    auth_basic off;
    proxy_pass http://127.0.0.1:8020/v1/user/;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Forwarded-Host $host;
    proxy_connect_timeout 10s;
    proxy_read_timeout 60s;
    proxy_send_timeout 60s;
}
~~~

**قبل از هر تغییر nginx:**

~~~bash
cp /etc/nginx/sites-available/wallex /etc/nginx/sites-available/wallex.bak.$(date +%Y%m%d_%H%M%S)
nginx -t && systemctl reload nginx
~~~

### خط سرخ‌ها

**دست نزن:**
- `/var/www/noosharp` (پورت 8000 + 3000)
- `/var/www/mabacheha` (8012)
- `/var/opt/nourin` (8015)
- DBهای `noosharp`, `noosharp_db`, `nourin_db`
- `.env` سرور (`chmod 600`)
- پورت‌های Wallex: فقط `8020` + `3020`

---

## 📦 User Paper Flow

**فاز ۱۷.۷.۲/۳** — paper state برای کاربر لاگین‌شده.

### Endpointها (`/v1/user/paper-v3/*`)

| متد | مسیر | نیاز |
|-----|------|------|
| GET | `/status` | JWT |
| GET | `/live` | JWT |
| POST | `/start` | JWT |
| POST | `/stop` | JWT |
| POST | `/reset` | JWT |
| POST | `/order` | JWT + engine فعال (409 اگر نه) |
| POST | `/position/{symbol}/close` | JWT + engine فعال |

### معماری

~~~
app/infrastructure/paper_trading/
├── protocol.py           ← PaperRepositoryProtocol (async)
├── repository.py         ← PaperRepository (async facade, asyncio.to_thread)
├── user_repository.py    ← UserPaperRepository (DB-backed)
├── engine.py             ← PaperEngine (base, ensure_state)
└── user_engine.py        ← UserPaperEngine (subclass)

app/presentation/api/v1/
└── user.py               ← ۷ endpoint
~~~

### State در DB

**ستون‌های `users` (view آماری):**
- `capital_total` — سرمایه کل (تغییرناپذیر توسط repo)
- `capital_available` — نقد (= `state.capital`)
- `capital_in_use`
- `open_positions` (JSONB)
- `closed_trades` (JSONB) — = `state.recent_trades`
- `equity_curve` (JSONB)
- `total_trades`, `wins`, `losses`

**ستون `paper_meta` (JSONB):**
- `initial_capital`, `equity`, `peak_capital`, `peak_equity`
- `max_drawdown_pct`, `total_pnl`, `total_pnl_pct`, `win_rate`
- `is_running`, `started_at`, `last_check_at`, `check_count`
- `events`, `radar`

### قاعده‌ی sync

⚠️ **همه‌ی تغییرات state فقط از طریق `UserPaperRepository.save()`.**

هیچ‌جا `session.execute(update(User))` مستقیم نزن — `paper_meta` desync می‌شه.

~~~python
# ❌ اشتباه
await session.execute(update(User).where(User.id == user_id).values(capital_available=100))

# ✅ درست
state.capital = 100
await repo.save(state)
~~~

### تفاوت با Guest

| مورد | Guest | User |
|------|-------|------|
| Storage | `data/guests/{token}/state.json` | DB (`users` + `paper_meta`) |
| Auth | `X-Guest-Token` | `Authorization: Bearer <JWT>` |
| Engine | خودکار ساخته می‌شه | باید `start` کنه (`409 no_engine`) |
| Scheduler key | token string | UUID |
| Repo | `PaperRepository` (فایل) | `UserPaperRepository` (DB) |

### Test pattern

~~~python
# tests/integration/test_user_paper_api.py
from httpx import ASGITransport, AsyncClient

@pytest.fixture
async def client():
    async with app.router.lifespan_context(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            yield c

@pytest.fixture(autouse=True)
async def _dispose():
    yield
    await engine.dispose()  # جلوگیری از loop desync
~~~


