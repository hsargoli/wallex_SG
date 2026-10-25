# 🗺️ ویژگی‌های فاز بعد (پس از MVP)

> این سند، ایده‌های پذیرفته‌شده برای فاز بعد از لانچ MVP را ثبت می‌کند.
> هر آیتم: مشکل، راه‌حل پیشنهادی، تصمیم CTO، تاریخ.

---

## ۱. WebSocket برای کندل‌ها (جایگزین REST /v1/udf/history)

**مشکل:** والکس REST (`/v1/udf/history`) برای ۲ نماد (`PUMPTMN`, `USOONTMN`) ناپایداره (timeout مکرر). حتی prefetch + retry + stale fallback، کاربر برای این ۲ نماد ۸s صبر می‌کنه.

**راه‌حل:** استفاده از WebSocket والکس (اگر ارائه می‌ده) برای live candles. یا اتصال WebSocket داخلی (که در `ticker_ws.py` برای ticker استفاده شده) برای کندل‌ها.

**تصمیم CTO (2026-10-25):** فاز بعد. اولویت متوسط. placeholder: TBD.

**بدهی مرتبط:** `top_n=50` hardcoded در `config.py` — بعد از websocket، شاید غیرضروری بشه.

---

## ۲. Cache as Port (DDD Fix)

**مشکل:** `application/use_cases/get_candles.py` مستقیم از `infrastructure/cache/candles.py` import می‌کنه. نقض dependency rule.

**راه‌حل:** `domain/ports/cache.py` (Protocol)، پیاده‌سازی در infrastructure، inject در use_case.

**تصمیم CTO (2026-10-24):** فاز بعد از MVP. بدهی فنی مستند.

---

## ۳. LRU Eviction برای Cache

**مشکل:** `CandlesCache` entryها رو هرگز evict نمی‌کنه (`_store` بی‌نهایت رشد می‌کنه، هرچند bounded با تعداد نمادها).

**راه‌حل:** LRU با ظرفیت (مثلاً ۱۰۰۰ entry).

**تصمیم CTO:** فاز بعد. برای MVP، ~۴۰۰ symbol × payload کوچک = چند MB، قابل قبول.

---

## ۴. `/list` — فیلتر نمادهای نامعتبر batch

**مشکل:** `/v1/scanner/list` نمادهایی مثل `STMN`, `ZECTMN`, `SUITMN` برمی‌گردونه که `/signals/batch` با 422 ردشون می‌کنه.

**راه‌حل:** فیلتر در `/list` یا در فرانت قبل از فرستادن به batch.

**تصمیم CTO:** deferred. اثری بر performance نداره.

---

## ۵. Dynamic Import برای Chartها (Frontend)

**مشکل:** `lightweight-charts` (~۵۰۰KB) در همه‌ی صفحه‌ها eager لود می‌شه، حتی صفحه‌ی اصلی.

**راه‌حل:** `next/dynamic` با `ssr: false` برای chart components.

**تصمیم CTO (2026-10-25):** **فاز فعلی — بعد از Prefetch.**

---
