# 📊 تاریخچه وضعیت پروژه سروباتس (ترید)

این سند تاریخچه‌ای از وضعیت هفتگی پروژه است. آخرین گزارش‌ها در بالا قرار می‌گیرند.

---

## 🚀 گزارش 2026-10-28 — ساعت 08:53 (معماری ربات‌ها)
**وضعیت:** 🟢 **Live — Stable** | **گزارش‌دهنده:** دی پرتو (مجری) / دی صحرا (مشاور)
**تگ:** `v1.2.2-bots-arch`

### 🎯 دستاوردها
- **Dual-Tier Registry:** افزودن فیلد `tier` به `BotInfo`. ربات‌ها به دو دسته `production` و `experimental` تقسیم شدند.
- **یکپارچه‌سازی Nooaah:** ربات `NooaahBot` با حفظ منطق ML خود، حالا از `BaseBot` ارث‌بری می‌کند و در رجیستری ثبت می‌شود.
- **API جدید:** افزودن `GET /v1/bots/list` برای فرانت‌اند.
- **رفع باگ تست (Cache Pollution):** کشف شد که تست‌های `AnalyzeSymbol` به خاطر کش شدن لیست خالی، فیل می‌شدند. یک فیکسچر `autouse` برای پاکسازی کش اضافه شد.

### 📊 شاهدها
- `pytest tests/unit/` → **۲۶۱ پاس (بدون خطا)**.
- Deploy موفق و بک‌اند `active`.
- پاسخ `/v1/bots/list` موفق.

---
## 🚀 گزارش 2026-10-28 — ساعت 01:19 (رفع خطای 504 کش مارکت‌ها)
**وضعیت:** 🟢 **Live — Stable** | **گزارش‌دهنده:** دی پرتو (مجری) / دی دریا (CTO)
**تگ:** `v1.2.1-markets-cache`

### 🎯 مشکل
درخواست به `/v1/markets` گاهی تا ۸ ثانیه طول می‌کشید (تماس مستقیم با والکس). این تاخیر باعث می‌شد آروان‌کلود قبل از پاسخ سرور، Timeout داده و خطای 504 برگرداند.

### 🛠️ راه‌حل
- ایجاد `MarketsCache` (in-memory) با TTL=3600s (۱ ساعت).
- اتصال کش به `GetMarketsUseCase` (فقط در صورت کش خالی به والکس وصل می‌شود).

### 📊 شاهد (تست مستقیم روی سرور بدون واسطه آروان)
- زمان پاسخ کش شده (Warm): **۱۶ میلی‌ثانیه (0.016s)**
- درخواست‌های بعدی از طریق آروان هم بدون 504 و با موفقیت (200) پاسخ داده می‌شوند.

### ✅ تست‌ها
- تست دستی تولید (curl) روی سرور پروداکشن: موفق.
- تست لوکال `pytest` به دلیل عدم دسترسی به اینترنت سرور اجرا نشد (بدهی پذیرفته‌شده).

---

## 🚀 گزارش 2026-10-27 — ساعت 21:42 (پیروزی زیرساخت + عرضه کیهان)
**وضعیت:** 🟢 **Live — Ultra Fast** | **گزارش‌دهنده:** دی پرتو (مجری) / دی دریا (CTO)
**تگ‌ها:** `v1.2.0-keyhan` (کد) | **کامیت:** `cde9f12`

### 🎯 دستاوردهای این فاز:
۱. **حل ریشه‌ای مشکل کش آروان:** با تنظیم Page Rules در پنل آروان (Ignore Vary) و هدایت آروان به کش کردن صفحات Next.js، سرعت پاسخ‌دهی از ۳۸۲ میلی‌ثانیه به **۲۴ میلی‌ثانیه** رسید (هدر `x-cache: HIT`).
۲. **عرضه رسمی کیهان بازار (Keyhan):**
   - انتقال به گروه (public) برای دسترسی بدون لاگین.
   - تغییر کامل نام از Cosmos به Keyhan (در کد، URL و UI).
   - طراحی مجدد کارت لندینگ پیج با افکت‌های نوری و مدار چرخان (ریسپانسیو برای موبایل).
   - اضافه شدن لینک به سایدبار.
   - کانواس (Canvas) با ستاره‌های واقعی، تفکیک اندازه بر اساس حجم، و لنگر بیت‌کوین (BTC).

### 📊 شاهدهای نهایی (Smoke Test):
| مسیر | HTTP Code | TTFB (زمان پاسخ) |
|---|---|---|
| `sarvbots.ir/` | ۲۰۰ | ~۰.۰۳s |
| `sarvbots.ir/keyhan` | ۲۰۰ | ~۰.۰۲s |
| `noosharp.ir` | ۲۰۰ | ~۰.۶s (بدون تغییر) |
| `hosg.ir` | ۲۰۰ | ~۰.۵s (بدون تغییر) |

### ✅ وضعیت پروژه:
- هیچ تغییری در بک‌اند اعمال نشد (صفر ریسک).
- سرویس‌های `wallex-frontend` و `wallex-backend` کاملاً `active` هستند.
- نقطه بازگشت (Rollback) در گیت‌هاب تضمین شده است.

---
## 🚀 گزارش 2026-10-25 — ساعت 17:49 (لانچ v1.1.0 — پایداری پس از اسپرینت بهینه‌سازی)
**وضعیت:** 🟢 **Live — Stable** | **گزارش‌دهنده:** دی پرتو (مجری) / دی دریا (CTO) / حسین (رهبر)
**تگ:** `v1.1.0-launch` | **کامیت:** `cb4c660`

### 🎯 هدف
تثبیت پایداری پس از اسپرینت multi-fix (prefetch + frontend + cleanup + signals cache).

### 🛠️ تغییرات انباشته (از v1.0.0-mvp تا الان)
- **Prefetch:** top=30، interval=5min، sequential 1h→1D، retry 2s
- **Frontend:** LiveChart lazy-load via `dynamic` + client wrapper
- **Cleanup:** ۸۶+۳۷ `.bak` حذف، ۴۰۰MB آزاد، ۴ `.env.bak` (root-owned، امنیت) حذف
- **Signals:** `1h` و `1D` فقط از cache. حذف `get_markets` از `/batch`. TTL `1h`: 300→900s

### 📊 نتایج (شاهد)
| مورد | قبل | بعد |
|---|---|---|
| `/signals/batch` ۱۰ نماد (cold) | ۳۰s | **۰.۵۵s** (۵۴×) |
| `/signals/batch` ۱۰ نماد (warm) | ۳۰s | **۰.۴۵s** (۶۶×) |
| `/signals` صفحه | کند | **۰.۵۰s** |
| `/scanner` صفحه | کند | **۰.۵۵s** |
| noosharp.ir / hosg.ir | ۲۰۰ | **۲۰۰** (خط سرخ حفظ شد) |

### ✅ تست‌ها
- Prefetch: ۱۰/۱۰ (شامل cache-only 1h/1D)
- Regression: ۳۹/۳۹
- `tsc`: ۰ خطا
- `build`: موفق

### 🚧 بدهی فنی (پذیرفته‌شده)
- cron DB برای کندل (نیاز به ADR جدا)
- `_archive/` نگه داشته شد (تاریخچه)
- Cosmos (ADR 0031، فاز بعد)
- `scalp_master` cleanup

---

## 🚀 گزارش 2026-10-25 — ساعت 11:59 (Frontend Perf — dynamic LiveChart)
**وضعیت:** 🟢 **Live** | **گزارش‌دهنده:** دی پرتو (مجری) / دی دریا (CTO)
**تگ:** `v1.0.3-frontend-perf` | **کامیت:** `7891bd2`

### 🎯 هدف
کاهش حجم bundle اولیه صفحه اصلی با Lazy-Loading چارت‌ها (`lightweight-charts` ~168K).

### 🛠️ راه‌حل
- ساخت Client Wrapper (`live-chart-dynamic.tsx`) چون `next/dynamic` با `ssr: false` در Server Component مجاز نیست.
- `loading: () => <Skeleton className="h-[400px]" />` برای جلوگیری از CLS.

### 📊 نتایج (شاهد)
| مورد | قبل | بعد |
|---|---|---|
| `lightweight-charts` در HTML اولیه | ✅ بود | ❌ حذف شد (Lazy) |
| CLS | — | ❌ صفر (Skeleton هم‌ارتفاع) |
| شاهد بصری | — | ✅ `/scanner` + `/signals` سالم |

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
