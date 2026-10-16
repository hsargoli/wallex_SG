# Wallex — معماری احراز هویت (Auth)

> این سند، طراحی سیستم ثبت‌نام + ورود SarvBots رو توضیح می‌ده.
> تاریخ: 2026-10-16
> وضعیت: طراحی (پیاده‌سازی نشده)
> مرتبط: [`GUEST_MODE.md`](./GUEST_MODE.md) v2.1

---

## 🎯 هدف

**مراحل کاربری SarvBots:**

| مرحله | چطور | پول مجازی | پول واقعی | ذخیره |
|-------|------|-----------|-----------|-------|
| **۱. مهمان** | خودکار (guest-token) | ۵۰۰ هزار تومان | ❌ | localStorage + JSON file |
| **۲. ثبت‌نام‌شده** | ایمیل + پسورد | **۳ میلیون تومان** | ❌ | PostgreSQL |
| **۳. متصل به والکس** | + توکن والکس | **۵ میلیون تومان** | سرمایه‌ی خودش | PostgreSQL (AES-256) |

**این سند، مرحله ۲ و پایه‌ی ۳ رو طراحی می‌کنه.**

---

## 🏗️ معماری

~~~
┌─────────────────────────────────────────────────┐
│  Frontend (Next.js)                              │
│  /register  →  فرم ثبت‌نام                      │
│  /login     →  فرم ورود                         │
│  Header     →  نمایش user/guest + logout        │
└─────────────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────┐
│  Backend (FastAPI) — /v1/auth/*                  │
│  POST /register   → {user_token, capital_total} │
│  POST /login      → {user_token, capital_total} │
│  GET  /me         → user info                   │
│  POST /logout     → invalidate (اختیاری)        │
│  POST /merge-from-guest → انتقال state مهمان    │
└─────────────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────┐
│  PostgreSQL 14 (روی سرور)                        │
│  Database: wallex_db                            │
│  Tables: users, register_attempts               │
└─────────────────────────────────────────────────┘
~~~

---

## 🗄️ مدل داده (PostgreSQL)

### جدول `users`

~~~sql
CREATE TABLE users (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email         VARCHAR(255) UNIQUE NOT NULL,

    -- Auth
    password_hash VARCHAR(255) NOT NULL,   -- bcrypt

    -- پول مجازی (شبیه‌سازی)
    capital_total     NUMERIC(20, 2) DEFAULT 3000000.00,
    capital_available NUMERIC(20, 2) DEFAULT 3000000.00,
    capital_in_use    NUMERIC(20, 2) DEFAULT 0.00,

    -- state (mirroring PaperState)
    open_positions  JSONB DEFAULT '[]'::jsonb,
    closed_trades   JSONB DEFAULT '[]'::jsonb,
    equity_curve    JSONB DEFAULT '[]'::jsonb,

    -- آمار
    total_trades  INTEGER DEFAULT 0,
    wins          INTEGER DEFAULT 0,
    losses        INTEGER DEFAULT 0,

    -- اتصال والکس (فاز بعد)
    wallex_token_encrypted  BYTEA,
    wallex_connected_at     TIMESTAMPTZ,

    -- متادیتا
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW(),
    last_seen_at TIMESTAMPTZ DEFAULT NOW(),
    is_active   BOOLEAN DEFAULT TRUE
);

CREATE INDEX idx_users_email ON users (LOWER(email));
CREATE INDEX idx_users_created ON users (created_at DESC);
~~~

### جدول `register_attempts` (rate limit ۱/روز/IP)

~~~sql
CREATE TABLE register_attempts (
    id           BIGSERIAL PRIMARY KEY,
    ip_address   INET NOT NULL,
    email        VARCHAR(255) NOT NULL,
    success      BOOLEAN DEFAULT FALSE,
    attempted_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_register_attempts_ip_time
    ON register_attempts (ip_address, attempted_at DESC);
~~~

**قاعده:** ۱ ثبت‌نام موفق در ۲۴ ساعت اخیر per IP.

---

## 🔐 Auth Flow

### ۱. ثبت‌نام

**Request:**
~~~
POST /v1/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "min-8-chars",
  "guest_token": "..." | null   ← اختیاری، برای merge
}
~~~

**Server:**
1. Validate email + password (min 8 chars)
2. Check rate limit (۱/روز/IP)
3. Check email unique
4. Hash password (bcrypt cost=12)
5. Insert user
6. اگه guest_token هست → merge state مهمان
7. Generate JWT (7 روز)
8. Return `{user_token, capital_total, merged}`

**Response:**
~~~json
{
  "user_token": "eyJ...",
  "capital_total": 3000000.0,
  "merged": true,
  "merged_from_guest": true
}
~~~

### ۲. ورود

**Request:**
~~~
POST /v1/auth/login
{
  "email": "user@example.com",
  "password": "..."
}
~~~

**Server:**
1. Find user by email (LOWER)
2. Verify password (bcrypt)
3. Update `last_seen_at`
4. Generate JWT

**Response:** مثل register (بدون merged)

### ۳. JWT Structure

~~~json
{
  "sub": "user-uuid",
  "email": "user@example.com",
  "role": "user",
  "iat": 1792139524,
  "exp": 1792744324
}
~~~

- **الگوریتم:** HS256
- **کلید:** `JWT_SECRET_KEY` در `.env` (۳۲+ بایت random)
- **انقضا:** ۷ روز
- **Refresh:** ❌ (JWT بلندمدت برای MVP کافیه)
- **Logout:** فقط `localStorage.removeItem("sarvbots_user_token")` + redirect به `/`
- **⚠️ نکته:** چون JWT statelessـه، logout سمت server معنایی نداره. توکن تا انقضا معتبرـه. برای MVP قابل قبوله.

---

## 🔄 Merge state مهمان → کاربر

**سناریو:** کاربر اول مهمانه، سفارش می‌ده، بعد ثبت‌نام می‌کنه.

**منطق:**
~~~
1. کاربر ثبت‌نام می‌کنه + guest_token می‌فرسته
2. Server:
   a. چک می‌کنه آیا guest_token موجودـه (data/guests/{token}/)
   b. اگه بله:
      - capital_available = 3M + guest.capital_available
      - open_positions = guest.open_positions (ادغام)
      - closed_trades = guest.closed_trades (ادغام)
   c. guest dir پاک می‌شه
3. Response: merged: true
~~~

**⚠️ نکته:** پول مهمان (۵۰۰K) به ۳M اضافه می‌شه (نه جایگزین). یعنی کاربر جدید ممکنه ۳.۵M داشته باشه اگه state مهمانش کامل باشه.

**✅ تصمیم نهایی (2026-10-16): گزینه A**

**پول جدید = ۳ میلیون + پول مهمان**

- اگه مهمان state داشت (۵۰۰K کامل) → **۳.۵M**
- اگه مهمان خرج کرده بود → ۳M + باقی‌مونده‌ی مهمان
- positions و closed_trades هم ادغام می‌شن

**چرا این؟**
- کاربر انگیزه‌ی ثبت‌نام قبل از خرج کردن داره
- حس «پول من هدر نرفت» می‌ده
- ساده برای توضیح: «هر چی داشتی، به ۳M اضافه می‌شه»

---

## 🌐 Frontend UX

### صفحه‌ی `/register`

~~~
┌───────────────────────────────────────┐
│  ثبت‌نام                              │
│                                        │
│  ایمیل:  [__________________]          │
│  پسورد:  [__________________]          │
│  تکرار:  [__________________]          │
│                                        │
│  ☑ انتقال دارایی مهمان به این حساب    │
│                                        │
│  [ثبت‌نام]                             │
│                                        │
│  حساب داری؟ [ورود]                    │
└───────────────────────────────────────┘
~~~

**بعد از موفقیت:**
- ذخیره user_token در localStorage
- پاک کردن guest_token
- redirect به `/dashboard`

### صفحه‌ی `/login`

ساده‌تر:
~~~
ایمیل:  [____]
پسورد:  [____]
[ورود]
حساب نداری؟ [ثبت‌نام]
~~~

### Header

**مهمان:**
~~~
[بج: مهمان] [دکمه: ثبت‌نام]
~~~

**کاربر:**
~~~
[بج: user@example.com] [دکمه: خروج]
~~~

---

## 🔒 امنیت

| مورد | پیاده‌سازی |
|------|-----------|
| پسورد | bcrypt (cost=12) |
| JWT | HS256 + secret ۳۲ بایت |
| Rate limit ثبت‌نام | ۱/روز/IP |
| Rate limit login | ۵/دقیقه/IP (SlowAPI) |
| HTTPS | اجباری (آروان) |
| CORS | محدود به `sarvbots.ir` |
| fail2ban | ۴۰۱ روی `/login` → بلاک |

### 🔑 Password Policy

**الزامات:**
- حداقل **۸ کاراکتر**
- بدون نیاز به عدد/حرف بزرگ/علامت خاص (MVP)

**💡 توضیح آموزشی در فرم ثبت‌نام:**

> **چرا پسورد قوی مهمه؟**
>
> هرچی پسورد شما قوی‌تر باشه، احتمال اینکه کسی بتونه وارد حسابتون بشه کمتره.
> ما از **bcrypt** برای ذخیره‌ی پسورد استفاده می‌کنیم — یعنی حتی اگه دیتابیس ما هک شه، پسورد شما قابل خواندن نیست.
>
> **پیشنهاد:**
> - از یه پسورد طولانی استفاده کن (مثلاً یه جمله)
> - پسوردت رو با هیچ سرویس دیگه‌ای share نکن
> - از یه password manager استفاده کن (مثل Bitwarden)

**Validation:**
- Backend: `min_length=8` در Pydantic
- Frontend: نمایش زنده‌ی «حداقل ۸ کاراکتر» + راهنمای امنیتی

**⚠️ در فاز بعد:**
- تأیید ایمیل (فاز ۱۸)
- فراموشی پسورد (فاز ۱۸)
- OTP پیامکی (فاز ۱۹)

---

## 🚦 فازبندی پیاده‌سازی

| فاز | کار | زمان |
|-----|-----|------|
| ۱۷.۳ | Schema + Migration (alembic) | ۱-۲ ساعت |
| ۱۷.۴ | Backend: register + login + JWT | ۲-۳ ساعت |
| ۱۷.۵ | Backend: merge state | ۱-۲ ساعت |
| ۱۷.۶ | Frontend: `/register` + `/login` + Header | ۲-۳ ساعت |
| ۱۷.۷ | Deploy + تست end-to-end | ۱ ساعت |
| **۱۷.۸** | **اتصال توکن والکس (۵M مجازی)** | **۴-۶ ساعت** |

**جمع:** ~۱۲-۱۸ ساعت

---

## ✅ تصمیم‌های نهایی (2026-10-16)

| سؤال | تصمیم |
|------|-------|
| **Merge پول مهمان** | ۳M + پول باقی‌مونده‌ی مهمان (معمولاً ۳.۵M) |
| **پول ثبت‌نام** | ۳M مجازی |
| **پول با توکن** | ۵M مجازی + دسترسی به ترید واقعی |
| **تأیید ایمیل** | فاز بعد (۱۷.۸ یا فاز ۱۸) |
| **Password policy** | حداقل ۸ کاراکتر + توضیح آموزشی |
| **Session** | JWT ۷ روز (بدون refresh) |
| **Logout** | پاک کردن localStorage + redirect |

---

## 🔗 لینک‌های مرتبط

- [`GUEST_MODE.md`](./GUEST_MODE.md) — معماری مهمان
- [`../deployment/README.md`](../deployment/README.md) — deployment
- [`../ARCHITECTURE.md`](../ARCHITECTURE.md) — معماری کد (DDD)

---

**آخرین آپدیت:** 2026-10-16
**نسخه:** 1.1 (طراحی — تصمیم‌های نهایی)
