# Wallex — معماری حالت مهمان (Guest Mode)

> این سند، طراحی حالت مهمان (Guest) برای پلتفرم Wallex رو توضیح می‌ده.
> هدف: کاربران بدون توکن والکس، بتونن پلتفرم رو با پول مجازی تجربه کنن.
> تاریخ: 2026-10-14
> وضعیت: طراحی (پیاده‌سازی نشده)

---

## 🎯 هدف

**مهمان (بدون توکن والکس) باید بتونه:**
- چارت‌ها، قیمت‌ها، عمق بازار رو ببینه (public data)
- سیگنال‌ها، اسکنر، تحلیل رو ببینه (محاسبه‌ی خودمون)
- Nooaah رو با **پول مجازی** (۵۰۰K تومان) تجربه کنه
- سفارش ثبت کنه (شبیه‌سازی، نه واقعی)
- پولش کم و زیاد شه (مثل paper trading واقعی)

**مهمان نباید بتونه:**
- به حساب واقعی کسی دسترسی داشته باشه
- دارایی‌های حسین یا کاربران دیگه رو ببینه
- معامله‌ی واقعی کنه

---

## 🏗️ معماری سه‌لایه

```
┌─────────────────────────────────────────────────┐
│  ۱. PUBLIC (بدون auth)                          │
│  - WebSocket: wss://api.wallex.ir/ws             │
│  - /v1/public/markets, signals, scanner          │
└─────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────┐
│  ۲. GUEST (anonymous session)                   │
│  - /v1/guest/*  (با guest-token)                │
│  - Nooaah paper, portfolio مجازی                │
└─────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────┐
│  ۳. USER (authenticated)                        │
│  - /v1/user/*  (با user-token)                  │
│  - Account واقعی، Nooaah live                   │
└─────────────────────────────────────────────────┘
```

---

## 👤 لایه‌ی ۱: Public

**بدون هیچ auth.**

### WebSocket (والکس، عمومی)

- **URL:** `wss://api.wallex.ir/ws`
- **کانال‌ها:**
  - `all@price` → قیمت همه‌ی بازارها
  - `MARKET@buyDepth` → عمق بازار
  - `MARKET@trade` → معاملات اخیر

**نکته:** frontend **مستقیم** به این WebSocket وصل می‌شه (بدون proxy از backend).

### Backend Endpoints

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
- cache توی Redis یا in-memory

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
   - اگه state نبود → ۵۰۰,۰۰۰ تومان پول مجازی
۵. frontend: guest-token توی localStorage ذخیره می‌کنه
```

### Guest Endpoints

```
POST /v1/guest/anonymous      → guest-token جدید
GET  /v1/guest/me             → اطلاعات مهمان
GET  /v1/guest/portfolio      → سبد مجازی
GET  /v1/guest/nooaah/status  → وضعیت Nooaah paper
POST /v1/guest/nooaah/kill    → توقف
POST /v1/guest/nooaah/resume  → ادامه
GET  /v1/guest/trades         → تاریخچه‌ی معاملات مجازی
```

### State Management

**جدول `guest_states` (PostgreSQL):**

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
```

**Cleanup:** state مهمان‌هایی که ۳۰ روز inactive هستن، پاک می‌شن.

### Nooaah Paper (مشترک)

**معماری:**
- **یه scheduler مشترک** — همه‌ی guestها رو توی یه loop پردازش می‌کنه
- **یه WebSocket مشترک** به والکس — fan-out به guestها
- **per-guest state** توی DB

**چرا مشترک؟** چون:
- منابع سرور محدوده
- ۱۰۰۰ مهمان × scheduler جدا = غیرممکن
- یه loop، همه رو پردازش می‌کنه

**چرخه:**
```
هر ۳۰ دقیقه:
  for guest in active_guests:
    candles = fetch_candles(guest.symbol)
    signal = strategy.propose_trade(candles)
    if signal:
      executor.paper_execute(guest, signal)
      update guest_state in DB
```

---

## 🔐 لایه‌ی ۳: User (Authenticated)

**با ثبت‌نام (ایمیل + پسورد).**

### ثبت‌نام

```
POST /v1/user/register
{
  "email": "user@example.com",
  "password": "hashed_with_bcrypt"
}
→ { "user_token": "JWT..." }
```

**امنیت:**
- پسورد: `bcrypt` یا `argon2`
- ایمیل: تأیید (اختیاری برای فاز اول)
- rate limiting: برای جلوگیری از abuse

### ورود

```
POST /v1/user/login
{
  "email": "user@example.com",
  "password": "..."
}
→ { "user_token": "JWT..." }
```

### اتصال توکن والکس

```
POST /v1/user/wallex/connect
Authorization: Bearer <user_token>
{
  "wallex_token": "..."  ← توکن والکس کاربر
}
→ { "status": "connected" }
```

**امنیت:**
- توکن والکس، **رمزنگاری‌شده** توی DB ذخیره می‌شه (AES-256)
- کلید رمزنگاری: توی `.env` سرور (`WALLEX_TOKEN_ENCRYPTION_KEY`)
- توکن والکس، **هرگز** به frontend برنمی‌گرده

### User Endpoints

```
GET  /v1/user/me              → اطلاعات کاربر
GET  /v1/user/portfolio       → سبد واقعی
GET  /v1/user/account/*       → حساب واقعی
GET  /v1/user/nooaah/status   → Nooaah live
POST /v1/user/nooaah/kill     → توقف
POST /v1/user/nooaah/resume   → ادامه
POST /v1/user/logout          → خروج
```

---

## 🔄 تبدیل مهمان → کاربر

**وقتی مهمان، ثبت‌نام می‌کنه:**

```
۱. POST /v1/user/register (email + password)
۲. backend:
   - کاربر جدید ساخته می‌شه
   - اگه guest-token داشت → state مهمان به کاربر منتقل می‌شه (merge)
   - guest-token باطل می‌شه
۳. user-token برمی‌گرده
۴. frontend: user-token توی localStorage
```

**Merge state:**
- `capital_total`، `open_positions`، `closed_trades` → منتقل می‌شن
- اگه کاربر قبلاً state داشت → جمع می‌شن (یا reset)

---

## 🌐 Frontend UX

### صفحه‌ی اصلی (مهمان)

```
┌────────────────────────────────────────────────┐
│  🎭 حالت مهمان                                  │
│                                                 │
│  پول مجازی: ۵۰۰,۰۰۰ تومان                       │
│  ⚠️ این دارایی فقط توی این مرورگر ذخیره شده     │
│                                                 │
│  [ثبت‌نام]  ← برای:                            │
│    • دسترسی از همه‌ی دستگاه‌ها                   │
│    • پول مجازی دائمی                            │
│    • تجربه‌ی بهتر                                │
│                                                 │
│  [ورود با توکن والکس]  ← برای:                  │
│    • معامله‌ی واقعی                              │
│    • دسترسی کامل                                │
└────────────────────────────────────────────────┘
```

### داشبورد مهمان

- چارت‌ها (WebSocket مستقیم)
- سیگنال‌ها، اسکنر
- Nooaah paper (پول مجازی)
- portfolio مجازی

### داشبورد کاربر

- همه‌ی مهمان +
- portfolio واقعی
- Nooaah live
- تنظیمات حساب

---

## 🔒 امنیت

| لایه | اقدام |
|------|-------|
| **داده‌ی public** | Cache، rate limit |
| **Guest** | guest-token (UUID، غیرقابل حدس) |
| **User** | JWT + bcrypt |
| **Wallex token** | AES-256 encryption، فقط سرور |
| **Rate limiting** | SlowAPI (قبلاً توی requirements بود) |
| **HTTPS** | اجباری (آروان) |
| **Basic Auth** | برای admin/دسترسی محدود (فعلاً) |

---

## 📊 مقیاس‌پذیری

### چالش‌ها

| چالش | راه‌حل |
|------|-------|
| **۱۰۰۰ مهمان** | scheduler مشترک، WebSocket مشترک |
| **State** | PostgreSQL (نه JSON files) |
| **WebSocket** | fan-out از یه اتصال |
| **Cache** | Redis (یا in-memory) |
| **Rate limit** | SlowAPI + آروان |

### آینده (اگه رشد کرد)

- migrate به Kubernetes
- Redis cluster
- PostgreSQL replication
- CDN برای static assets (آروان)

---

## 🚦 فازبندی پیاده‌سازی

### فاز ۱: Backend — Public Layer

- `/v1/public/*` endpoints
- WebSocket عمومی (اگه لازم)
- Cache

### فاز ۲: Backend — Guest Layer

- `POST /v1/guest/anonymous`
- جدول `guest_states`
- `/v1/guest/*` endpoints
- Nooaah paper (scheduler مشترک)

### فاز ۳: Frontend — Guest UX

- صفحه‌ی اصلی مهمان
- localStorage برای guest-token
- داشبورد مهمان
- Nooaah paper UI

### فاز ۴: Backend — User Layer

- `POST /v1/user/register` + login
- جدول `users`
- `/v1/user/*` endpoints
- Wallex token encryption

### فاز ۵: Frontend — User UX

- صفحه‌ی ثبت‌نام / ورود
- اتصال توکن والکس
- داشبورد کاربر (live)

### فاز ۶: Merge (مهمان → کاربر)

- انتقال state
- ابطال guest-token

---

## ❓ سؤال‌های باز

1. **Redis یا in-memory cache؟** (فعلاً in-memory، بعداً Redis)
2. **ایمیل تأیید:** فاز اول یا بعداً؟
3. **Rate limit:** چقدر؟ (مثلاً ۱۰۰ request/دقیقه per guest)
4. **Cleanup:** ۳۰ روز inactive؟ یا بیشتر؟
5. **Merge:** اگه کاربر قبلاً state داشت، جمع یا reset؟
6. **Nooaah paper symbol:** چه نمادهایی؟ (پیش‌فرض: BTC، ETH، ...)

---

## 🔗 لینک‌های مرتبط

- [`../deployment/README.md`](../deployment/README.md) — معماری deployment
- [`../ARCHITECTURE.md`](../ARCHITECTURE.md) — معماری کد (DDD)
- [`../AI_PROJECT_GUIDE.md`](../AI_PROJECT_GUIDE.md) — راهنمای AI

---

**آخرین آپدیت:** 2026-10-14
**نسخه:** 1.0 (طراحی)
