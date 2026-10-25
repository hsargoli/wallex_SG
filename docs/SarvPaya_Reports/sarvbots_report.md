# 📊 تاریخچه وضعیت پروژه سروباتس (ترید)

این سند تاریخچه‌ای از وضعیت هفتگی پروژه است. آخرین گزارش‌ها در بالا قرار می‌گیرند.

---

## 🚀 گزارش 2026-10-25 — ساعت 11:38 (Prefetch — ۹۶٪ cache hit)
**وضعیت:** 🟢 **Live** | **گزارش‌دهنده:** دی پرتو (مجری) / دی دریا (CTO)
**تگ:** `v1.0.2-prefetch` | **کامیت:** `c0eda11`

### 🎯 هدف
رفع cold start در `/signals/batch`. بار اول بعد از restart، ۱۰ نماد × ۲ TF × ۸s = ~۸۰s. کش بعد از کاربر اول کمک می‌کرد، ولی اولین کاربر منتظر می‌موند.

### 🛠️ راه‌حل
- `app/services/prefetch.py` — `CandlePrefetcher` (asyncio task در lifespan)
- top_n=50، interval=600s (~۲۶٪ بار والکس، CTO-approved)
- Sequential 1h → 1D (parallel با `gather`، `1h` رو از گرسنگی timeout می‌کرد)
- 1D limit=31 (حداقل برای `change_1m` که به `daily[-31]` نیاز داره)
- Retry ۱ بار با ۲s backoff (والکس برای `PUMPTMN`/`USOONTMN` ناپایداره)
- structlog برای observability (`extra` visible)
- `WALLEX_TIMEOUT_SECONDS`: 30 → 15 (در `/home/deploy/wallex/.env`)

### 📊 نتایج (شاهد — سرور `c0eda11`)
| سناریو | قبل | بعد |
|---|---|---|
| `/signals/batch` ۱۰ نماد (cold) | ۱۶.۷s | ۸.۹s (۲ نماد ناپایدار) |
| `/signals/batch` ۲۰ نماد (warm) | ۱۶.۷s | **۰.۵۷s** ⚡ |
| `/scanner/scan` (shared cache) | ۸.۵s | **۰.۴s** |
| prefetch cycle | — | `symbols=50, calls=100` |

### ⚠️ نمادهای ناپایدار در والکس
- **`PUMPTMN`**, **`USOONTMN`**: timeout مکرر روی `/v1/udf/history` (همیشه، نه فقط امروز).
- **راه‌حل فعال:** `stale fallback` (کاربر ۸s صبر، بعد داده‌ی قدیمی).
- **تصمیم CTO:** hardcode استثنا ممنوع. websocket در `NEXT_FEATURES.md` ثبت شد.

### ✅ Test-first
- ۷ تست (`test_prefetch.py`) — شامل `limit=31`, retry, sequential
- Regression: ۳۶/۳۶

### 🚧 بدهی فنی
- Application → infrastructure import مستقیم (مثل `_PNL_CACHE`). DDD fix: cache as Port.
- websocket برای کندل‌ها (فاز بعد).
- `/list` شامل نمادهای نامعتبر batch (STMN, ZECTMN) — pre-existing، deferred.

---

## 🚀 گزارش 2026-10-24 — ساعت 23:03 (بهبود عملکرد ۱۳-۳۳ برابر)
**وضعیت:** 🟢 **Live — با cache**
**گزارش‌دهنده:** دی پرتو (مجری) / دی دریا (CTO)
**تگ:** `v1.0.1-perf` | **کامیت:** `19b63ba`

### 🎯 مشکل
`/signals/batch` برای ۱۰ نماد، ۱۶.۷s طول می‌کشید (cold). ریشه:
- `GetCandlesUseCase` بدون cache (هر request → والکس)
- `WALLEX_TIMEOUT_SECONDS=4` ولی wallex p95 ~۸s → nginx 504

### 🛠️ راه‌حل
- `app/infrastructure/cache/candles.py` — in-memory cache (TTL per timeframe: 15m=60s, 1h=300s, 4h=600s, 1D=3600s). Pattern: `_PNL_CACHE` in `services/wallex/service.py:309`. workers=1 → in-memory safe.
- Wire در `GetCandlesUseCase` (check before fetch, set before return)
- `WALLEX_TIMEOUT_SECONDS`: 4 → 15

### 📊 نتایج (شاهد — سرور `19b63ba`)
| سناریو | قبل | بعد | بهبود |
|--------|-----|-----|-------|
| ۱ نماد cold | ۹s | ۹s | — (بار اول) |
| ۱ نماد warm | ۹s | **۰.۶۶s** | **۱۳.۶×** |
| ۱۰ نماد cold | ۱۶.۶s | ۱۶.۶s | — (بار اول) |
| ۱۰ نماد warm | ۱۶.۶s | **۰.۵۰s** | **۳۳.۳×** |
| Scanner (shared cache) | ۸.۵s | **۰.۴s** | **۲۱×** |

### ✅ Test-first
- `test_candles_cache.py` — ۸ تست. RED: ۱ failed (assert 2==1). GREEN: ۸/۸.
- Regression: ۳۹/۳۹ passed.

### 🚧 بدهی فنی (پذیرفته‌شده)
- Application layer مستقیم infrastructure رو import می‌کنه (مثل `_PNL_CACHE`). DDD fix = cache as Port — فاز بعد.
- Cold start هنوز کند (۸-۱۶s). Cron pre-fetch — فاز بعد (CTO decision).

### ⚠️ گزارش جدا (خارج از wallex)
- `mabacheha.ir`: SSL handshake failure (`sslv3 alert`, TLS 1.2/1.3 mismatch) — از قبل، خط سرخ، مال ما نیست
- `noosharp.ir`: nginx log `connect() failed 111` روی 8000/3000 — از قبل

---

## 🏆 گزارش 2026-10-23 — ساعت 22:01 (تأیید نهایی قطعی)
**وضعیت:** 🚀 **لانچ عمومی صادر شد (Public Launch)**
**تأییدکننده:** دی تعیین‌گر (مستقل)

### ✅ حکم نهایی
🟢 **تأیید قطعی — برای نسخه سرور `046249f` (همگام با لوکال).**
مجوز شروع فاز عمومی صادر شد.

### 🔍 شاهدهای تأیید نهایی
- **همگام‌سازی:** سرور و لوکال روی کامیت `046249f` (تأیید شد).
- **Smoke Test:** Home=200, Login=200, Dashboard=200, Backend=200.
- **تست‌ها:** ۳۶۷ تست Passed.
- **سرویس‌ها:** `wallex-backend` و `wallex-frontend` (active).
- **توکن‌ها:** جدول `auth_tokens` = ۰ رکورد (پاکسازی شد).
- **Nginx:** مسیرها و `server_name` تأیید شد (Drift کاهش یافت).

### 📌 بدهی‌های فنی مستند (غیرمسدودکننده)
1. **SMTP Mock:** نقص پذیرفته‌شده (تصمیم مدیرعامل برای MVP).
2. **لاگ Backend:** نیاز به دسترسی `sudo journalctl` (بدهی مستندسازی).

### 🎯 خارج از دامنه
- نوشارپ، نورین، صرافی بین‌المللی، پرداخت ریالی.

---
*سروباتس با موفقیت به مرحله لانچ عمومی رسید.*
