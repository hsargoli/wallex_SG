# 0030. Security Baseline (Auth, Rate Limit, Token Lifecycle, Test Policy)

**Status:** Accepted
**Date:** 2026-10-20
**Deciders:** Hossein, Di Sheida, Di Darya, Di Sahra, Di Ferdows, Di Barakeh

## Context
با رشد پروژه و اضافه شدن قابلیت‌های امنیتی در Sprintهای اخیر، نیاز به یک "نقطه مرجع امنیتی" (Baseline) حس می‌شد تا از تکرار باگ‌های گذشته (مثل نشت توکن‌های قدیمی یا تست‌های fail پنهان) جلوگیری شود. این سند تصمیمات کلیدی امنیتی، تست و استقرار را تثبیت می‌کند.

## Decision

### ۱. Token Lifecycle (چرخه حیات توکن)
- تمام توکن‌های JWT حاوی فیلد `token_version` هستند.
- هر تغییری در رمز عبور (`change-password` و `reset-password`) باید `token_version` کاربر را در دیتابیس یک واحد افزایش دهد تا تمام JWTهای قبلی در دستگاه‌های دیگر باطل شوند.
- یک endpoint اختصاصی `/logout-all` وجود دارد که به کاربر اجازه می‌دهد با افزایش `token_version` از تمام دستگاه‌ها خارج شود.

### ۲. Rate Limit Strategy (استراتژی محدودیت نرخ)
- از کتابخانه `SlowAPI` با ذخیره‌سازی In-Memory برای MVP استفاده می‌شود (با قابلیت مهاجرت به Redis در آینده).
- **الزام ساختاری:** هر endpoint که از `@limiter.limit` استفاده می‌کند **باید** پارامترهای `request: Request` و `response: Response` را در امضای خود داشته باشد (طبق ADR 0028).
- برای endpointهای حساس (wallet, auth)، از استراتژی **Hybrid Rate Limit (`user_id:ip`)** استفاده می‌شود تا از دور زدن محدودیت با تغییر IP جلوگیری شود. (پیاده‌سازی شده در `get_user_and_ip`).
- **محدودیت‌ها:** `CHANGE_PASSWORD` (5/hour)، `RESET_PASSWORD` (5/hour)، `CONNECT` (5/hour)، `LOGIN` (5/minute).

### ۳. Email Verification Policy (`is_verified`)
- **MVP (فعلی):** از حالت `soft-warning` استفاده می‌شود. کاربران تایید نشده می‌توانند به کیف پول متصل شوند، اما در پاسخ API فیلد `warning: "email_not_verified"` دریافت می‌کنند. (دلیل: پیاده‌سازی سرویس Resend).
- **آینده (بعد از پایداری کامل):** تغییر به `hard-enforce` و بازگرداندن خطای `403 Forbidden` برای عملیات‌های حساس.

### ۴. Test Isolation & Policy (سیاست تست)
- **الزام Event Loop:** تمام تست‌های Async که با دیتابیس کار می‌کنند، باید در teardown خود `await engine.dispose()` را صدا بزنند تا از خطای `Event loop is closed` جلوگیری شود.
- **الزام State Reset:** Rate Limiter باید قبل از هر تست ریست شود (فایل `conftest.py`).
- **الزام Fixture:** استفاده از هش واقعی bcrypt (نه رشته‌های فیک) در فیکسچرها الزامی است.
- **Fail-Fast:** در CI، تست‌ها با فلگ `-x` اجرا می‌شوند.

### ۵. CI/CD & Deployment Policy
- **GitHub Actions:** پایپ‌لاین‌های CI (بک‌اند و فرانت‌اند) برای هر push و PR اجرا می‌شوند.
- **Local Hook:** به دلیل محدودیت پلن رایگان GitHub در ریپازیتوری‌های Private (عدم اجرای Branch Protection)، یک **Pre-push Hook** در سمت لوکال تنظیم شده است که تا تست‌های بک‌اند پاس نشوند، اجازه‌ی `git push` نمی‌دهد.
- **Deployment:** هر تغییر قبل از استقرار باید وارد گیت شده و از طریق CI تایید شود.

### ۶. Witness Requirement for Claims (درس‌آموخته)
- **قانون:** هیچ ادعای امنیتی (چه مثبت و چه منفی) بدون ارائه شاهد (خروجی `grep`، لاگ تست، یا کد مشخص) پذیرفته نیست.
- **چرا؟** در این دوره، چندین ادعای بحرانی توسط اعضای تیم (حتی ناظر امنیت) مطرح شد که با شاهد کد رد شدند (مثل نبودن password confirmation یا مرده بودن route). این بند تضمین می‌کند که تصمیمات فقط بر اساس داده‌های عینی گرفته شوند.

## Consequences
- **Positive:** شفافیت کامل امنیتی، جلوگیری از بازگشت باگ‌ها، و ایجاد یک محیط توسعه امن برای AIهای بعدی.
- **Negative:** پیچیدگی بیشتر در نوشتن تست‌ها و نیاز به رعایت دقیق Decoratorها در FastAPI.

## References
- ADR 0027 (Auth Tokens & Email Port)
- ADR 0028 (Rate Limit Strategy)
- `backend/app/core/rate_limit.py`
- `backend/app/services/auth_recovery.py`
