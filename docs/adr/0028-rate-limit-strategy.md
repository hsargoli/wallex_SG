# 0028. Rate Limit Strategy & SlowAPI Integration

**Status:** Accepted
**Date:** 2026-10-19
**Deciders:** Hossein, Di Sahra, Di Darya, Di Ferdows

## Context
برای جلوگیری از حملات Brute-force روی لاگین و درخواست‌های مخرب (مثل اسپم کردن فراموشی رمز)، نیاز به محدودیت نرخ (Rate Limit) داریم. ما از کتابخانه `SlowAPI` استفاده می‌کنیم.

## Decision
- **کتابخانه:** از `SlowAPI` با ذخیره‌سازی در حافظه (In-Memory) برای MVP استفاده می‌کنیم. در فاز بعدی (در صورت افزایش مقیاس)، می‌توانیم به Redis مهاجرت کنیم.
- **الزام ساختاری:** به دلیل فعال بودن `headers_enabled=True` در `rate_limit.py`، **تمامی Endpointهایی که از `@limiter.limit` استفاده می‌کنند الزاماً باید پارامتر `response: Response` را در امضای خود داشته باشند.** در غیر این صورت، SlowAPI کرش می‌کند و خطای ۵۰۰ می‌دهد. (این باگ در Sprint 2 کشف و مستند شد).
- **محدودیت‌های فعلی:**
  - `LOGIN_LIMIT`: 5 درخواست در دقیقه (برای جلوگیری از Brute-force).
  - `FORGOT_PASSWORD_LIMIT`: 3 درخواست در دقیقه (برای جلوگیری از اسپم ایمیل).
  - `PLACE_ORDER_LIMIT`: 5 درخواست در دقیقه.

## Consequences
- **Positive:** امنیت بالا در برابر حملات ساده، پیاده‌سازی سریع و بدون نیاز به زیرساخت Redis.
- **Negative:** در صورت اجرای چندین Worker (Multi-worker) روی یک سرور، محدودیت‌ها به صورت سراسری اعمال نمی‌شوند (چون در حافظه‌ی هر پروسه ذخیره می‌شوند). این مورد برای MVP قابل قبول است.

## References
- `backend/app/core/rate_limit.py`
- `backend/app/presentation/api/v1/auth.py`
- `backend/app/presentation/api/v1/orders.py`
