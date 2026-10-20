# 🩺 Incident Report: token_version NameError on Login

**تاریخ:** 2026-10-20
**نویسنده:** دی برکه
**وضعیت:** حل شد (Resolved)
**شدت:** بالا (کاربران با رمز صحیح نمی‌توانستند لاگین کنند)

## خلاصه

`create_user_token()` در payload JWT به `token_version` ارجاع می‌داد،
ولی پارامترش را در signature نداشت. نتیجه: NameError روی هر لاگین
موفق → HTTP 500.

## کشف

journalctl هیچ traceback نشان نمی‌داد چون
`StandardOutput=append:/var/log/wallex-backend.log` بود.
با خواندن فایل لاگ، traceback واقعی پیدا شد:

    File ".../app/core/auth.py", line 56, in create_user_token
        "token_version": token_version,
    NameError: name 'token_version' is not defined

## ریشه‌یابی

Feature `token_version` (invalidate JWT روی تغییر رمز) نصفه پیاده شده بود:
- migration `d4e5f6g7h8i9` اعمال شده ✅
- `user.py` فیلد دارد ✅
- `create_user_token()` پارامتر ندارد ❌
- `decode_user_token()` نسخه را validate نمی‌کند ❌ (feature کامل نیست)

## چرا تست‌های قبلی باگ را ندیدند

تست‌های rate limit با رمز اشتباه بودند → 401 قبل از رسیدن به
`create_user_token` → باگ مخفی ماند.

درس: تست negative (رمز اشتباه) باگ positive (رمز درست) را پنهان می‌کند.

## Fix (commit 410d2d7)

    # core/auth.py
    def create_user_token(user_id: str, email: str, token_version: int = 1) -> str:

    # services/auth/service.py — 2 callers (register + login)
    token = create_user_token(str(user.id), user.email, user.token_version)

## تأیید

- checksum سرور = لوکال: f0ca05da / 756bebf6 ✅
- systemctl: active ✅
- log tail: Application startup complete — بدون Traceback ✅
- login واقعی: HTTP 200 + token_len 269 ✅
- production: /, /login → 200؛ /dashboard → 307 (redirect طبیعی) ✅

## درس‌ها

۱. تست negative + positive، هر دو.
۲. StandardOutput=append → journald نمی‌بیند؛ فایل لاگ را بخوان.
۳. Feature نصفه = باگ فعال.
۴. scp هدفمند جای rsync کلی.
۵. بعد از fix، login واقعی تست کن — نه فقط health check.

## کارهای باقی‌مونده

- drift سرور: ۲۰ فایل modified + ۶ untracked
- `decode_user_token` validation ناقص
- ADR دیپلوی (از دیروز باز است)

«آهسته، مطمئن، با شاهد، با بازبینی، با مهربانی.»
