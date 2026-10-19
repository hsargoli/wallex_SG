# 0027. Auth Tokens and Email Sender Port

**Status:** Accepted
**Date:** 2026-10-19
**Deciders:** Hossein, Di Sahra, Di Ferdows

## Context
برای Sprint 2 (Auth & Security)، نیاز به پیاده‌سازی فراموشی رمز عبور و تایید ایمیل داریم. برای این کار به دو زیرساخت نیاز است:
۱. ذخیره‌سازی امن توکن‌های موقت (Reset/Verify).
۲. ارسال ایمیل که در محیط لوکال تست‌پذیر باشد (بدون وابستگی به سرویس‌های بیرونی).

## Decision
- **AuthTokens:** یک جدول جدید به اسم `auth_tokens` ساخته می‌شود (Aggregate جداگانه). توکن‌ها به صورت هش‌شده (`token_hash`) با الگوریتم SHA-256 ذخیره می‌شوند تا در صورت نفوذ دیتابیس، توکن‌ها قابل استفاده نباشند.
- **EmailSender:** از الگوی Hexagonal (Port/Adapter) استفاده می‌کنیم. یک `EmailSenderPort` در دامنه تعریف می‌شود. در محیط لوکال از `MockEmailSender` (چاپ در ترمینال) و در پروداکشن از `ResendEmailSender` استفاده خواهد شد.
- فیلد `is_verified` به جدول `users` اضافه می‌شود.

## Consequences
- **Positive:** امنیت بالا، تست‌پذیری عالی در لوکال، و عدم وابستگی کدهای دامنه به سرویس‌های ایمیل.
- **Negative:** پیچیدگی بیشتر در ساختار پوشه‌ها نسبت به روش‌های ساده.

## References
- `backend/app/domain/entities/auth_token.py`
- `backend/app/domain/ports/email_sender.py`
