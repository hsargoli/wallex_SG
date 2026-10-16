# Wallex — معماری حالت مهمان (Guest Mode) — v2.1

> این سند، طراحی حالت مهمان (Guest) برای پلتفرم Wallex رو توضیح می‌ده.
> هدف: کاربران بدون توکن والکس، بتونن پلتفرم رو با پول مجازی تجربه کنن.
> تاریخ: 2026-10-14
> وضعیت: طراحی (پیاده‌سازی نشده)
> نسخه‌ی قبلی: [`archive/GUEST_MODE_v1.md`](./archive/GUEST_MODE_v1.md)

---

## 📝 تغییرات v2.1 (2026-10-15)

> این بخش، تصمیم‌های پیاده‌سازی رو بر اساس شناخت معماری فعلی کد می‌نویسه.
> بدنه‌ی v2.0 (پایین) هنوز معتبرـه، ولی در جزئیات فنی به‌روزرسانی شده.

### ۱. معماری Paper Engine — Multi-tenant (راه A)

**تصمیم:** PaperEngine فعلی multi-tenant می‌شه (نه کلاس جدید).

**دلیل:** PaperRepository از قبل state_dir param داره. فقط یه خط تغییر توی PaperEngine کافیه.

~~~python
# app/infrastructure/paper_trading/engine.py
class PaperEngine:
    def __init__(self, ..., state_dir: Path | None = None):
        self.repo = PaperRepository(state_dir=state_dir) if state_dir else PaperRepository()
~~~

**نتیجه:**
- /v1/paper-v3/* (برای کاربر) → state_dir=None → همون رفتار قبلی
- /v1/guest/paper-v3/* (برای مهمان) → state_dir=Path(f"data/guests/{token}")

### ۲. Storage — per-guest JSON

~~~
backend/data/
├── paper_v3/state.json          ← کاربر (بدون تغییر)
└── guests/{token}/state.json    ← مهمان
~~~

**چرا JSON نه DB؟** MVP سریع‌تر، PaperRepository از قبل JSON می‌نویسه.

### ۳. Guest Token

- UUID v4 (random)
- ذخیره: localStorage مرورگر
- اولین بار: POST /v1/guest/anonymous
- بدون auth (session موقت)

### ۴. Endpoints مهمان

~~~
POST /v1/guest/anonymous       → { guest_token, capital_total: 500000 }
GET  /v1/guest/me              → اطلاعات مهمان
GET  /v1/guest/paper-v3/status
GET  /v1/guest/paper-v3/live
POST /v1/guest/paper-v3/start
POST /v1/guest/paper-v3/stop
POST /v1/guest/paper-v3/reset
~~~

### ۵. Scheduler مشترک

یه loop، هر ۱۸۰ ثانیه، همه‌ی guest engineها رو پردازش می‌کنه.
(۱۰۰۰ مهمان × task جدا = منابع سرریز)

### ۶. Nooaah Live — دست نمی‌خوره

- services/bots/nooaah/ → بدون تغییر
- PaperExecutor Nooaah → بدون تغییر
- app.state.paper_v3_engine → بدون تغییر

### ۷. Frontend Guest UX

- تشخیص خودکار: چک localStorage برای guest_token
- در هدر: «حالت مهمان» + دکمه‌ی «ثبت‌نام»
- صفحات: داشبورد، Nooaah paper، portfolio مجازی

### ۸. امنیت

| مسیر | دسترسی |
|------|--------|
| / , /demo | عمومی |
| /api/v1/guest/* | با guest-token (UUID) |
| /api/v1/paper-v3/* | Basic Auth (فعلاً) |
| /api/v1/account/* | Basic Auth (فعلاً) |
| /ws/* | عمومی |

### ۹. زنجیره‌ی ارتقا

~~~
مهمان (guest-token) → ثبت‌نام → کاربر (user-token) → اتصال والکس → live
~~~

---

---

## 🎯 هدف

**پلتفرم Wallex، سه مرحله‌ی کاربری داره:**

| مرحله | چیکار می‌کنه | توکن والکس | پول |
|-------|-------------|-----------|-----|
| **۱. مهمان** | بدون ثبت‌نام، فقط تجربه | ❌ | ۵۰۰,۰۰۰ تومان مجازی (localStorage) |
| **۲. ثبت‌نام‌شده** | ایمیل + پسورد | ❌ | ۳,۰۰۰,۰۰۰ تومان مجازی (PostgreSQL) |
| **۳. متصل به والکس** | + توکن والکس | ✅ | سرمایه‌ی واقعی |

**هدف:** کاربر، بدون ترس از امنیت، مرحله‌به‌مرحله وارد شه:
- اول تجربه کنه (مهمان)
- بعد ثبت‌نام کنه (پول مجازی بیشتر)
- آخر توکن والکس بده (live trading)

---

## 🏗️ معماری سه‌لایه

```
┌─────────────────────────────────────────────────┐
│  ۱. PUBLIC (بدون auth)                          │
│  - WebSocket: wss://api.wallex.ir/ws             │
│    (all@price, MARKET@buyDepth, MARKET@trade)    │
│  - /v1/public/markets, signals, scanner          │
└─────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────┐
│  ۲. GUEST (anonymous session)                   │
│  - guest-token (UUID در localStorage)           │
│  - ۵۰۰K تومان مجازی                              │
│  - /v1/guest/*  (paper trading)                 │
└─────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────┐
│  ۳. USER (authenticated)                        │
│  - user-token (JWT)                             │
│  - ۳M تومان مجازی (paper)                     │
│  - /v1/user/*                                   │
│                                                  │
│  ┌───────────────────────────────────────────┐ │
│  │  ۳.۵ USER + WALLEX (wallex connected)     │ │
│  │  - + wallex_token (AES-256 encrypted)     │ │
│  │  - live trading (سرمایه‌ی واقعی)           │ │
│  └───────────────────────────────────────────┘ │
└─────────────────────────────────────────────────┘
```

**نکته:** لایه‌ی ۳.۵، همون لایه‌ی ۳ـه، ولی با توکن والکس متصل.

---

## 👤 لایه‌ی ۱: Public

**بدون هیچ auth.**

### WebSocket (والکس، عمومی)

- **URL:** `wss://api.wallex.ir/ws`
- **کانال‌ها:**
  - `all@price` → قیمت همه‌ی بازارها
  - `MARKET@buyDepth` → عمق بازار
  - `MARKET@trade` → معاملات اخیر

**معماری:** frontend **مستقیم** به این WebSocket وصل می‌شه (بدون proxy از backend).

**چرا مستقیم؟**
- ✅ سبک‌تر (بدون بار روی backend)
- ✅ latency کمتر
- ✅ cache خودکار (مرورگر)

### Backend Endpoints (Public)

```
GET /v1/public/markets           → لیست بازارها
GET /v1/public/markets/{symbol}  → جزئیات یه بازار
GET /v1/public/signals           → سیگنال‌های محاسبه‌شده
GET /v1/public/scanner           → نتایج اسکنر
GET /v1/public/analysis/{symbol} → تحلیل یه نماد
```

**منبع داده:**
- WebSocket والکس (public)
- محاسبات خودمون (signals، scanner، analysis)
- cache: in-memory (فاز اول) / Redis (بعداً)

---

## 🎭 لایه‌ی ۲: Guest (Anonymous)

**بدون ثبت‌نام، خودکار.**

### جریان (Flow)

```
۱. کاربر، صفحه‌ی اصلی رو باز می‌کنه
۲. frontend: چک localStorage برای guest-token
   - اگه هست → استفاده
   - اگه نیست → POST /v1/guest/anonymous
۳. backend: guest-token جدید (UUID) می‌سازه
۴. backend: state مهمان رو توی PostgreSQL ذخیره می‌کنه
   - capital_total: 500,000 تومان
۵. frontend: guest-token توی localStorage ذخیره می‌کنه
۶. کاربر، داشبورد رو می‌بینه (با پول مجازی)
```

### Guest Endpoints

```
POST /v1/guest/anonymous      → guest-token جدید
GET  /v1/guest/me             → اطلاعات مهمان
GET  /v1/guest/portfolio      → سبد مجازی
GET  /v1/guest/nooaah/status  → وضعیت Nooaah paper
POST /v1/guest/nooaah/kill    → توقف
POST /v1/guest/nooaah/resume  → ادامه
GET  /v1/guest/trades         → تاریخچه‌ی معاملات
```

### پول مجازی مهمان

- **۵۰۰,۰۰۰ تومان** (پیش‌فرض)
- ذخیره: localStorage (guest-token) + PostgreSQL (state)
- **قابل تغییر** از پنل admin (بعداً)

### نمادهای Nooaah Paper (مهمان)

**۵ نماد:**
- BTC (بیت‌کوین)
- ETH (اتریوم)
- USDT (تتر)
- ADA (کاردانو)
- DOGE (دوج)

**قابل تغییر از پنل admin (بعداً).**

### هشدار localStorage

**توی داشبورد مهمان، این پیام نمایش داده می‌شه:**

```
⚠️ توجه:
- دارایی مجازی شما (۵۰۰,۰۰۰ تومان) فقط توی این مرورگر ذخیره شده
- اگه مرورگر رو پاک کنید، یا از حالت incognito استفاده کنید، دارایی از دست می‌ره
- برای دسترسی دائمی و از همه‌ی دستگاه‌ها، ثبت‌نام کنید
- ثبت‌نام به شما دارایی بیشتر و قابلیت بیشتری می‌ده
```

### Cleanup

**State مهمان‌های inactive (۳۰ روز) → پاک می‌شن.**

---

## 👥 لایه‌ی ۳: User (ثبت‌نام‌شده)

**با ثبت‌نام (ایمیل + پسورد). بدون توکن والکس.**

### ثبت‌نام

```
POST /v1/user/register
{
  "email": "user@example.com",
  "password": "..."
}
→ { "user_token": "JWT...", "capital_total": 3000000 }
```

**محدودیت:** ۱ ثبت‌نام/روز/IP (جلوگیری از حمله‌ی ربات‌ها).

**امنیت:**
- پسورد: `bcrypt` (hash)
- ایمیل: تأیید (فاز اول: بدون / فاز ۲: با تأیید)
- فراموشی پسورد: فاز اول: بدون / فاز ۲: با ایمیل

### ورود

```
POST /v1/user/login
{
  "email": "user@example.com",
  "password": "..."
}
→ { "user_token": "JWT..." }
```

### پول مجازی کاربر

- **۳,۰۰۰,۰۰۰ تومان** (پیش‌فرض)
- ذخیره: PostgreSQL (state)
- **قابل تغییر** از پنل admin (بعداً)

### نمادهای Nooaah Paper (کاربر)

**۷ نماد:**
- BTC, ETH, USDT, ADA, DOGE
- + BNB (بایننس کوین)
- + SOL (سولانا)

### User Endpoints (بدون والکس)

```
GET  /v1/user/me              → اطلاعات کاربر
GET  /v1/user/portfolio       → سبد مجازی (۲.۵M)
GET  /v1/user/nooaah/status   → وضعیت Nooaah paper
POST /v1/user/nooaah/kill     → توقف
POST /v1/user/nooaah/resume   → ادامه
GET  /v1/user/trades          → تاریخچه
POST /v1/user/logout          → خروج
```

---

## 🔐 لایه‌ی ۳.۵: User + Wallex (متصل)

**با توکن والکس. Live trading.**

### اتصال توکن والکس

```
POST /v1/user/wallex/connect
Authorization: Bearer <user_token>
{
  "wallex_token": "..."
}
→ { "status": "connected" }
```

**امنیت:**
- توکن والکس، **AES-256 encryption**، توی DB ذخیره می‌شه
- کلید رمزنگاری: توی `.env` سرور (`WALLEX_TOKEN_ENCRYPTION_KEY`)
- **توکن خام، هرگز توی DB نیست**
- **توکن خام، هرگز به frontend برنمی‌گرده**

### سرمایه

- **سرمایه‌ی واقعی کاربر** (از حساب والکس خودش)
- `WALLEX_API_KEY` کاربر → برای live trading

### نمادهای Nooaah Live (کاربر متصل)

**۱۰ نماد:**
- BTC, ETH, USDT, ADA, DOGE, BNB, SOL
- + XRP (ریپل)
- + MATIC (پالیگان)
- + DOT (پولکادات)

### User + Wallex Endpoints

```
GET  /v1/user/account/*           → حساب واقعی
GET  /v1/user/portfolio           → سبد واقعی
GET  /v1/user/nooaah/live/status  → Nooaah live
POST /v1/user/nooaah/live/kill    → توقف
POST /v1/user/nooaah/live/resume  → ادامه
POST /v1/user/wallex/disconnect   → قطع اتصال
```

---

## 🔄 تبدیل بین مراحل

### مهمان → ثبت‌نام‌شده

**وقتی مهمان، ثبت‌نام می‌کنه:**
```
۱. POST /v1/user/register (email + password)
۲. backend: کاربر جدید ساخته می‌شه
۳. اگه guest-token داشت → state مهمان به کاربر منتقل می‌شه (merge)
   - یا اگه کاربر قبلاً state داشت → فقط user state
   - تصمیم: اگه کاربر جدید بود، state مهمان → user
   - اگه کاربر قبلاً بود، state مهمان → دور ریخته
۴. guest-token باطل می‌شه
۵. user-token برمی‌گرده
```

### ثبت‌نام‌شده → متصل به والکس

**وقتی کاربر، توکن والکس می‌ده:**
```
۱. POST /v1/user/wallex/connect (wallex_token)
۲. backend: توکن رو validate می‌کنه (تست اتصال به والکس)
۳. اگه معتبر بود:
   - encrypt(wallex_token) → ذخیره توی DB
   - Nooaah live برای این کاربر فعال می‌شه
۴. اگه نامعتبر بود:
   - خطا برمی‌گرده
```

---

## 📊 مقایسه‌ی سه لایه

| ویژگی | مهمان | ثبت‌نام‌شده | متصل به والکس |
|-------|-------|------------|---------------|
| **ثبت‌نام** | ❌ | ✅ ایمیل | ✅ ایمیل |
| **توکن والکس** | ❌ | ❌ | ✅ |
| **پول مجازی** | ۵۰۰K | ۲.۵M | سرمایه‌ی خودش |
| **Nooaah paper** | ✅ | ✅ | ✅ |
| **Nooaah live** | ❌ | ❌ | ✅ |
| **نمادها** | ۵ | ۷ | ۱۰ |
| **دسترسی از همه‌ی دستگاه‌ها** | ❌ (localStorage) | ✅ | ✅ |
| **ذخیره‌ی state** | localStorage | PostgreSQL | PostgreSQL |
| **چرخه‌ی Nooaah** | ۱۰-۱۵ دقیقه | ۱۰-۱۵ دقیقه | ۳۰ دقیقه |

---

## 🚦 بخش دوم (در ادامه)

بخش دوم این سند شامل:
- پیاده‌سازی (DDD، Repository، Domain)
- مدل DB (PostgreSQL schema)
- امنیت (bcrypt، AES-256، rate limit)
- Frontend UX
- فازبندی پیاده‌سازی
- سؤال‌های باز

**به‌زودی اضافه می‌شه.**

---

## 🏛️ بخش دوم: پیاده‌سازی

> این بخش، جزئیات فنی پیاده‌سازی رو توضیح می‌ده:
> معماری کد (DDD)، مدل DB، امنیت، UX، فازبندی.

---

## 🏗️ معماری کد (DDD)

**سه لایه، طبق معماری فعلی Wallex:**

```
backend/app/
├── domain/                    ← منطق خالص (بدون وابستگی)
│   ├── user.py                ← User (entity)
│   ├── guest_state.py         ← GuestState (entity)
│   ├── user_state.py          ← UserState (entity)
│   └── repositories.py        ← interfaceها
│
├── application/               ← use caseها
│   ├── guest/
│   │   ├── anonymous.py       ← ساخت مهمان
│   │   └── paper_trading.py   ← Nooaah paper
│   ├── user/
│   │   ├── register.py        ← ثبت‌نام
│   │   ├── login.py           ← ورود
│   │   └── connect_wallex.py  ← اتصال توکن
│   └── public/
│       └── market_data.py     ← داده‌ی عمومی
│
├── infrastructure/            ← پیاده‌سازی
│   ├── postgres/
│   │   ├── models.py          ← SQLAlchemy models
│   │   ├── user_repo.py       ← PostgresUserRepository
│   │   └── guest_repo.py      ← PostgresGuestStateRepository
│   ├── wallex/
│   │   ├── client.py          ← والکس API client
│   │   └── ws.py              ← WebSocket
│   └── crypto/
│       ├── password.py        ← bcrypt
│       └── token.py           ← AES-256
│
└── api/                       ← endpoints (FastAPI)
    ├── public.py              ← /v1/public/*
    ├── guest.py               ← /v1/guest/*
    └── user.py                ← /v1/user/*
```

**اصول DDD:**
- **Domain:** خالص، بدون وابستگی به DB یا framework
- **Application:** use caseها، orchestration
- **Infrastructure:** پیاده‌سازی (PostgreSQL، والکس، crypto)
- **API:** لایه‌ی ورودی (FastAPI routers)

**Repository Pattern:**
```python
# domain/repositories.py
class UserRepository(Protocol):
    async def find_by_email(self, email: str) -> User | None: ...
    async def save(self, user: User) -> None: ...

# infrastructure/postgres/user_repo.py
class PostgresUserRepository:
    async def find_by_email(self, email: str) -> User | None:
        # SQLAlchemy query
        ...
```

**Domain، Repository رو می‌شناسه (interface)، ولی PostgreSQL رو نه.**

---

## 🗄️ مدل DB (PostgreSQL)

### جدول `users`

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,           -- bcrypt

    capital_total DECIMAL(20, 2) DEFAULT 3000000.00,
    capital_available DECIMAL(20, 2) DEFAULT 3000000.00,
    capital_in_use DECIMAL(20, 2) DEFAULT 0.00,

    open_positions JSONB DEFAULT '[]',
    closed_trades JSONB DEFAULT '[]',

    wallex_token_encrypted BYTEA,                  -- AES-256 (nullable)
    wallex_connected_at TIMESTAMP,

    mode VARCHAR(20) DEFAULT 'paper',
    killed BOOLEAN DEFAULT FALSE,

    created_at TIMESTAMP DEFAULT NOW(),
    last_seen_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users(email);
```

### جدول `guest_states`

```sql
CREATE TABLE guest_states (
    guest_token UUID PRIMARY KEY,
    created_at TIMESTAMP DEFAULT NOW(),
    last_seen_at TIMESTAMP DEFAULT NOW(),

    capital_total DECIMAL(20, 2) DEFAULT 500000.00,
    capital_available DECIMAL(20, 2) DEFAULT 500000.00,
    capital_in_use DECIMAL(20, 2) DEFAULT 0.00,

    open_positions JSONB DEFAULT '[]',
    closed_trades JSONB DEFAULT '[]',

    mode VARCHAR(20) DEFAULT 'paper',
    killed BOOLEAN DEFAULT FALSE
);

CREATE INDEX idx_guest_last_seen ON guest_states(last_seen_at);
```

### جدول `register_attempts` (برای محدودیت ۱/روز/IP)

```sql
CREATE TABLE register_attempts (
    id SERIAL PRIMARY KEY,
    ip_address INET NOT NULL,
    attempted_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_register_ip_time ON register_attempts(ip_address, attempted_at);
```

### Migration

**ابزار:** `alembic` (استاندارد SQLAlchemy).

```bash
alembic init migrations
alembic revision --autogenerate -m "add users, guest_states, register_attempts"
alembic upgrade head
```

---

## 🔒 امنیت

### پسورد کاربر

**Hash با bcrypt:**
```python
from passlib.hash import bcrypt

# hash
password_hash = bcrypt.hash(password)

# verify
is_valid = bcrypt.verify(password, password_hash)
```

**نکته:** bcrypt، salt خودکار اضافه می‌کنه. hash، غیرقابل برگشته.

### توکن والکس

**Encryption با AES-256 (Fernet):**
```python
from cryptography.fernet import Fernet

# کلید از .env
key = os.environ["WALLEX_TOKEN_ENCRYPTION_KEY"].encode()
f = Fernet(key)

# encrypt
encrypted = f.encrypt(wallex_token.encode())

# decrypt
wallex_token = f.decrypt(encrypted).decode()
```

**نکته:** توکن خام، فقط توی RAM (موقت). توی DB، همیشه encrypted.

### تولید کلید

**🖥️ سرور (root):**
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
# → کلید رو کپی کن توی .env
```

**توی `.env` سرور:**
```
WALLEX_TOKEN_ENCRYPTION_KEY=<32-byte-base64>
```

### JWT

**برای user-token و guest-token:**

```python
from jose import jwt

# sign
token = jwt.encode({"user_id": str(user.id), "role": "user"}, SECRET_KEY, algorithm="HS256")

# verify
payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
```

**`SECRET_KEY` توی `.env` سرور.**

### Rate Limit

**SlowAPI (قبلاً توی requirements بود):**
```python
from slowapi import Limiter

limiter = Limiter(key_func=get_remote_address)

@limiter.limit("100/minute")
async def guest_endpoint(...):
    ...
```

### محدودیت ثبت‌نام (۱/روز/IP)

```python
async def can_register(ip: str) -> bool:
    # چک کن توی ۲۴ ساعت گذشته، از این IP ثبت‌نام شده یا نه
    count = await db.execute(
        "SELECT COUNT(*) FROM register_attempts WHERE ip_address = :ip AND attempted_at > NOW() - INTERVAL '24 hours'",
        {"ip": ip}
    )
    return count.scalar() == 0
```

---

## 🎨 Frontend UX

### صفحه‌ی اصلی (مهمان)

```
┌────────────────────────────────────────────────┐
│  Wallex Platform                                │
│                                                 │
│  🎭 حالت مهمان                                  │
│                                                 │
│  دارایی مجازی: ۵۰۰,۰۰۰ تومان                    │
│  ⚠️ فقط توی این مرورگر ذخیره شده                │
│                                                 │
│  [ثبت‌نام کنید]  ← برای:                        │
│    • دارایی بیشتر (۳,۰۰۰,۰۰۰ تومان)             │
│    • دسترسی از همه‌ی دستگاه‌ها                   │
│    • نمادهای بیشتر (۷ به‌جای ۵)                 │
│                                                 │
│  [ورود با توکن والکس]  ← برای:                  │
│    • معامله‌ی واقعی                              │
│    • دسترسی کامل (۱۰ نماد)                      │
└────────────────────────────────────────────────┘
```

### داشبورد مهمان

- چارت‌ها (WebSocket مستقیم از والکس)
- سیگنال‌ها، اسکنر، تحلیل
- Nooaah paper (پول مجازی)
- portfolio مجازی
- **دکمه‌ی «ثبت‌نام» توی هدر**

### داشبورد کاربر (ثبت‌نام‌شده)

- همه‌ی مهمان +
- portfolio واقعی (۳M مجازی)
- Nooaah paper (۷ نماد)
- **دکمه‌ی «اتصال توکن والکس»**

### داشبورد کاربر (متصل)

- همه‌ی بالا +
- portfolio واقعی (سرمایه‌ی خودش)
- Nooaah live (۱۰ نماد)
- **دکمه‌ی «قطع اتصال»**

---

## 🚦 فازبندی پیاده‌سازی

### فاز ۱: Backend — Public Layer

- `/v1/public/*` endpoints
- cache in-memory
- rate limit

### فاز ۲: Backend — Guest Layer

- `POST /v1/guest/anonymous`
- جدول `guest_states`
- `/v1/guest/*` endpoints
- Nooaah paper (scheduler مشترک، ۱۰-۱۵ دقیقه)

### فاز ۳: Frontend — Guest UX

- صفحه‌ی اصلی مهمان
- localStorage برای guest-token
- داشبورد مهمان
- Nooaah paper UI

### فاز ۴: Backend — User Layer

- `POST /v1/user/register` + login
- جدول `users`
- `/v1/user/*` endpoints
- محدودیت ۱ ثبت‌نام/روز/IP

### فاز ۵: Frontend — User UX

- صفحه‌ی ثبت‌نام / ورود
- داشبورد کاربر (۲.۵M)
- Nooaah paper (۷ نماد)

### فاز ۶: Backend + Frontend — Wallex Connect

- `POST /v1/user/wallex/connect`
- AES-256 encryption
- Nooaah live (۱۰ نماد)
- داشبورد کاربر (live)

### فاز ۷: Merge (مهمان → کاربر)

- انتقال state
- ابطال guest-token

---

## ❓ سؤال‌های باز

**۱. ایمیل تأیید:** فاز ۱ یا بعداً؟
**۲. فراموشی پسورد:** فاز ۱ یا بعداً؟
**۳. Redis:** چه زمانی migrate از in-memory؟
**۴. Nooaah live:** scheduler per-user یا مشترک؟
**۵. Cleanup:** ۳۰ روز inactive — تأیید؟
**۶. Merge:** اگه کاربر قبلاً state داشت، جمع یا reset؟
**۷. WebSocket مستقیم:** اگه والکس قطع شد، fallback داریم؟
**۸. PWA:** آیا مهمان‌ها می‌تونن اپ نصب کنن؟

---

## 🔗 لینک‌های مرتبط

- [`archive/GUEST_MODE_v1.md`](./archive/GUEST_MODE_v1.md) — نسخه‌ی اول (تاریخچه)
- [`../deployment/README.md`](../deployment/README.md) — معماری deployment
- [`../ARCHITECTURE.md`](../ARCHITECTURE.md) — معماری کد (DDD)
- [`../AI_PROJECT_GUIDE.md`](../AI_PROJECT_GUIDE.md) — راهنمای AI

---

**آخرین آپدیت:** 2026-10-15
**نسخه:** 2.1 (طراحی)
**وضعیت:** طراحی — پیاده‌سازی نشده
