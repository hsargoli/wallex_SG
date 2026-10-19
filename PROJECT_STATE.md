# 🚦 وضعیت فعلی پروژه والکس (Project State)

**آخرین آپدیت:** 2026-10-19
**شاخه فعلی:** `refactor/full-ddd`
**تگ پایدار:** `v0.9.29-rate-limit-tests`

## 🎯 وضعیت MVP
**🏆 MVP والکس ۱۰۰٪ تکمیل شده است.**
هر سه اسپرینت (Sprint 1, 2, 3) کدنویسی، تست و روی پروداکشن (`sarvbots.ir`) دیپلوی شده‌اند.

| اسپرینت | موضوع | وضعیت |
|---------|-------|-------|
| Sprint 1 | Trade Token | ✅ ۱۰۰٪ |
| Sprint 2 | Auth & Security | ✅ ۱۰۰٪ |
| Sprint 3 | UI & Legal | ✅ ۱۰۰٪ |

## 📊 آمار فنی
- **تست‌های بک‌اند:** ۳۲۹ تست (Pytest) - ۱۰۰٪ پاس.
- **تست‌های فرانت‌اند:** TypeScript + ESLint بدون خطا.
- **معماری:** DDD + Hexagonal.
- **امنیت:** JWT، Fernet Encryption، Rate Limit با SlowAPI.

## 🤖 وضعیت ربات‌ها
- **Bear Hunter:** در حالت Paper Mode (تست با سرمایه ۵,۰۰۰,۰۰۰ تومان).

## ⚠️ بدهی‌های فنی (Technical Debt)
- **SMTP Production:** فعلاً ایمیل‌ها Mock هستند. باید قبل از لانچ عمومی، به یک سرویس واقعی (مثل Resend) وصل شود.
- **تست Verify Email:** تست‌های خودکار برای این بخش هنوز نوشته نشده است.
