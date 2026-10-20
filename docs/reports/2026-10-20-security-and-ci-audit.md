# 🛡️ گزارش جامع امنیت و زیرساخت — ۲۰۲۶-۱۰-۲۰

**نویسنده:** دی شیدا
**تیم:** سرو پایا رشد سبز
**وضعیت نهایی:** `8b64df9` + تغییرات CI (در حال دیباگ)

---

## 🎯 خلاصه‌ی اجرایی (Executive Summary)

این session با هدف بستن بدهی‌های فنی و امنیتی (که از دی برکه و دی دریا به جا مونده بود) شروع شد و با استقرار اولین **CI/CD Pipeline** پروژه به اوج رسید. 

**دستاوردهای کلیدی:**
۱. بستن ۳ شکاف امنیتی بحرانی (reset_password، change_password، logout-all).
۲. بازسازی زیرساخت تست‌ها (رفع ۸ تست شکسته‌ی پنهان و کشف باگ‌های Isolation).
۳. راه‌اندازی GitHub Actions برای جلوگیری از بازگشت این بدهی‌ها.
۴. تثبیت الگوی «شاهد مداری» (Witness Requirement) در بازبینی‌های تیمی.

---

## 🔒 ۱. اصلاحات امنیتی (Security Fixes)

### ۱.۱. باگ `reset_password` (بحرانی)
*   **مشکل:** تابع `auth_recovery.reset_password` فیلد `token_version` کاربر را افزایش نمی‌داد. اگر مهاجم JWT قربانی را دزدیده بود، با تغییر رمز توسط قربانی (Forgot Password)، JWT مهاجم هنوز معتبر می‌ماند.
*   **راه‌حل:** اضافه کردن `user.token_version = user.token_version + 1` به همراه `password_hash` در سرویس.
*   **تست:** `test_reset_password_invalidates_old_jwt` (تأیید 401 شدن JWT قدیمی).

### ۱.۲. Rate Limit برای `/change-password`
*   **مشکل:** این endpoint حساس (تغییر رمز) هیچ محدودیتی نداشت. مهاجم با JWT مسروقه می‌توانست رمز فعلی را Brute-force کند.
*   **راه‌حل:** تعریف `CHANGE_PASSWORD_LIMIT = "5/hour"` و افزودن `@limiter.limit` (منطبق با ADR 0028).
*   **تست:** `test_change_password_rate_limit_429_on_6th`.

### ۱.۳. endpoint جدید: `/logout-all`
*   **قابلیت:** خروج از تمام دستگاه‌ها با افزایش `token_version`.
*   **امنیت:** مجهز به rate limit (3/hour) + نیازمند JWT معتبر.
*   **تست:** ۳ تست (invalidation، بدون توکن، rate limit).

### ۱.۴. رفع بدهی تست‌های Password Confirmation
*   **مشکل:** کامیت `085b7a6` فیلد `password` را در `/connect` الزامی کرده بود، اما ۸ تست قدیمی آپدیت نشده بودند و بی‌صدا fail می‌شدند.
*   **راه‌حل:** 
    *   ریفکتور `wallex.py` برای استفاده از helper استاندارد `verify_password` (به جای `bcrypt.checkpw` مستقیم).
    *   اصلاح Fixture ها برای استفاده از هش واقعی bcrypt (به جای `test-hash-not-real`).
    *   آپدیت ۱۰ تست قدیمی + افزودن ۶ تست رگرسیون جدید.

---

## 🧪 ۲. زیرساخت تست (Test Infrastructure)

### ۲.۱. کشف باگ‌های Isolation (Event Loop Leak)
*   **درس:** اجرای همزمان تست‌های Async و FastAPI بدون مدیریت چرخه‌ی عمر (Lifespan) باعث خطای `Event loop is closed` می‌شود.
*   **راه‌حل:** الزامی کردن `await engine.dispose()` در teardown تمام تست‌های دیتابیس‌دار.

### ۲.۲. مدیریت State سراسری (SlowAPI)
*   **مشکل:** Rate Limiter در `slowapi` حافظه‌ی In-Memory دارد. اجرای ۱۴ بار `/connect` در تست‌ها باعث 429 شدن تست‌های بعدی می‌شد.
*   **راه‌حل:** افزودن فیکسچر `autouse` در `conftest.py` برای پاکسازی حافظه‌ی Limiter قبل از هر تست.

---

## ⚙️ ۳. زیرساخت CI/CD (GitHub Actions)

*   **مشکل کشف‌شده:** ۸ تست به مدت نامعلومی شکسته بودند و کسی متوجه نشده بود (چون CI وجود نداشت).
*   **راه‌حل:** ساخت `.github/workflows/test.yml`.
*   **وضعیت:** 🟢 **موفق (Test #3).** تمام ۷۹ تست بک‌اند و تایپ‌چک فرانت‌اند با موفقیت پاس شدند. (نیازمند افزودن ۳ کلید محیطی Dummy: `WALLEX_API_KEY`, `WALLEX_TOKEN_ENC_KEY`, `JWT_SECRET_KEY` در CI).
*   **ویژگی‌ها:**
    *   اجرای موازی بک‌اند (`pytest`) و فرانت‌اند (`tsc --noEmit`).
    *   راه‌اندازی سرویس موقت PostgreSQL 16 برای تست‌های بک‌اند.
    *   استفاده از `uv sync --frozen` و `npm ci` برای نصب دقیق پکیج‌ها.
    *   فعال‌سازی `-x` برای Fail-Fast.

---

## 🧠 ۴. درس‌های آموخته‌شده (Lessons Learned & Anti-Patterns)

### ۴.۱. الزام شاهد در بازبینی (Witness Requirement)
*   **مشاهده:** در جریان این session، ۴ ادعای بحرانی مطرح شد (نبود password confirmation، مرده بودن route، دو مسیر بودن wallex، گم شدن گزارش). تمام این ۴ ادعا با شاهد (grep/git) رد شدند.
*   **درس:** حتی ناظر امنیت (دی دریا) هم باید برای ادعاهایش `grep` یا کد بیاورد. **«هیچ ادعای امنیتی بدون یک خط شاهد، معتبر نیست.»** (این بند باید به ADR 0030 اضافه شود).

### ۴.۲. Anti-Pattern جدید: `!` در Commit Message
*   **مشکل:** استفاده از `!` در `git commit -m "..."` باعث فعال شدن History Expansion در bash و ناقص شدن پیام می‌شود.
*   **راه‌حل:** همیشه از `git commit -F- << 'MSG_EOF' ... MSG_EOF` استفاده کنید.

### ۴.۳. DDD در تست‌ها (Entity vs Model)
*   **درس:** در تست‌ها برای `session.add()` از مدل‌های دیتابیس (`AuthTokenModel`) یا ریپازیتوری‌ها استفاده کنید، نه Entity های دامنه (`AuthToken`). موجودیت‌های دامنه در SQLAlchemy مپ نمی‌شوند.

---

## 🚀 ۵. گام‌های بعدی (Next Steps)

*   **فوری:** دیباگ اولین اجرای CI (در حال انجام).
*   **کوتاه‌مدت (ADR 0030):** 
    *   تدوین سند Security Baseline با ۵ بند اصلی (Token Lifecycle، Rate Limit، Test Policy، is_verified، Deployment).
    *   تنظیم Branch Protection در GitHub (Merge Blocking).
*   **میان‌مدت:** 
    *   مهاجرت Rate Limit به Redis (برای Multi-worker).
    *   پیاده‌سازی Hybrid Rate Limit (`user_id:ip`).

---
**«آهسته، مطمئن، با شاهد، با بازبینی، با مهربانی.»** 🌿
