# 0017. Wallex Token Connection — اتصال حساب کاربر به والکس

**Status:** Accepted
**Date:** 2026-10-17
**Deciders:** حسین س، دی

## Context

فاز ۱۷.۷ (user paper state) تمام شد. کاربر می‌تونه:
- ثبت‌نام کنه
- Paper با ۳M مجازی بازی کنه
- سفارش دستی شبیه‌سازی کنه

ولی **هیچ اتصالی به حساب واقعی والکس نداره** — نه موجودی واقعی می‌بینه، نه می‌تونه معامله‌ی واقعی بزنه.

فاز ۱۷.۸ هدفش اینه: کاربر توکن API حساب Wallex خودش رو وارد کنه، ما اعتبارسنجی کنیم و ذخیره کنیم، و ازش برای:
- نمایش موجودی واقعی
- (فاز بعد) — معامله‌ی واقعی

### محدودیت‌های فعلی کد

بررسی `WallexExchange` (`app/infrastructure/exchange/wallex/client.py`):

- `create(settings)` — فقط از `settings.WALLEX_API_KEY` استفاده می‌کنه
- توکن سراسری (احتمالاً برای داده‌های عمومی، نه حساب کاربر)
- `get_balances()` بدون پارامتر توکن

`User` model (migration `291b79050370`):

- `wallex_token_encrypted: BYTEA | None` — آماده
- `wallex_connected_at: TIMESTAMPTZ | None` — آماده
- **نیاز به migration جدید نیست**

### انواع توکن والکس

والکس سه نوع توکن می‌ده:
- **View** (فقط-خواندن) — برای این فاز
- **Trade** — برای فاز ۱۷.۸.۴
- (نوع سوم — احتمالاً Read+Trade ترکیبی یا Admin)

فاز ۱۷.۸ فقط View token رو پشتیبانی می‌کنه. Trade token پذیرفته نمی‌شه (تا فاز بعد) — ولی از نظر ساختار DB می‌تونه ذخیره شه، فقط endpoint و UI هنوز trade رو غیرفعال می‌کنه.

## Decision

شش تصمیم کلیدی:

### تصمیم ۱: جریان کاربر — «ب+پ»

**گزینه‌ها:**
- الف) اجباری بعد از ثبت‌نام → کاربر paper-only مجبور می‌شه. ❌
- ب) اختیاری بعد از ثبت‌نام (با skip) ✅
- پ) کارت روی dashboard/settings ✅
- **ب+پ انتخاب شد**

**دلیل:** کاربر انتخاب داره (paper-only کافیه)، ولی هم شانس اولیه بعد از register داره (ب)، هم هر وقت خواست از settings برمی‌گرده (پ).

### تصمیم ۲: رمزنگاری — Fernet

**گزینه‌ها:**
- **الف) Fernet** (`cryptography.fernet.Fernet`) ✅
- ب) AESGCM مستقیم
- پ) رمزنگاری نامتقارن (RSA)

**دلیل:**
- Fernet: nonce + HMAC خودکار، foot-gun صفر، کد کمتر → ریسک کمتر
- برای use-case «یه بار نوشتن، هرازگاهی خوندن» کافیه
- کلید جدا `WALLEX_TOKEN_ENC_KEY` (نه JWT key) — اگه JWT چرخید، توکن‌ها سالم می‌مونن
- هزینه: ۱۰۰ بایت اضافی (برای توکن ۶۴ بایتی مهم نیست)

**کلید:**
~~~bash
# یک بار روی سرور:
WALLEX_TOKEN_ENC_KEY=$(python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
# → در /home/deploy/wallex/.env (کنار بقیه)
# → بکاپ در /root/db_backups/wallex_enc_key.bak (chmod 600)
~~~

⚠️ **اگه کلید گم شه:** همه‌ی کاربران باید دوباره توکن بدن. این رو در UI و پیام خطا شفاف می‌کنیم.

### تصمیم ۳: Reconnect — جایگزینی

**گزینه‌ها:**
- الف) رد کن با 409 «قبلاً متصل هستی»
- **ب) جایگزینی با اعتبارسنجی مجدد** ✅

**دلیل:** اگه کاربر توکنش رو revoke کرده یا expire شده، باید بتونه بدون قطع و وصل دستی، توکن جدید بده. ولی اعتبارسنجی مجدد قبل از ذخیره الزامیه.

### تصمیم ۴: Disconnect — فقط توکن

**گزینه‌ها:**
- **الف) فقط توکن پاک کن (تاریخچه می‌مونه)** ✅
- ب) همه‌ی تاریخچه‌ی والکس رو هم پاک کن

**دلیل:** تاریخچه‌ی معاملات (paper یا واقعی) مال کاربره، به حساب والکس وابسته نیست. فقط اتصال رو قطع می‌کنیم.

### تصمیم ۵: Paper Integration — مستقل

**گزینه‌ها:**
- **الف) paper با ۳M مجازی می‌مونه (مستقل)** ✅
- ب) paper از موجودی واقعی شروع کنه
- پ) کاربر انتخاب کنه

**دلیل:**
- Paper = آموزش و آزمایش، مستقل از پول واقعی
- اگه paper از موجودی واقعی شروع کنه، کاربر نمی‌تونه بی‌محابا آزمایش کنه
- درآمد واقعی کاربر روی paper تأثیر نمی‌ذاره (و برعکس)
- نمایش موجودی واقعی و paper کنار هم، در UI جدا هستند

### تصمیم ۶: WallexExchange — override کوچیک

**گزینه‌ها:**
- **الف) `create(settings, api_key=None)` — backward compatible** ✅
- ب) subclass جدا (`UserWallexExchange`)
- پ) `get_balances(token=...)` — فقط برای balances

**دلیل:** کمترین تغییر، صفر شکستن کد موجود.

~~~python
@classmethod
def create(cls, settings: Settings, api_key: str | None = None) -> WallexExchange:
    headers = {"x-api-key": api_key or settings.WALLEX_API_KEY}
    ...
~~~

### Endpoints

| متد | مسیر | توضیح |
|-----|------|-------|
| POST | `/v1/user/wallex/connect` | body: `{token: "..."}` — اعتبارسنجی + ذخیره‌ی رمزنگاری‌شده |
| DELETE | `/v1/user/wallex/disconnect` | پاک‌کردن توکن + `wallex_connected_at = NULL` |
| GET | `/v1/user/wallex/status` | `{connected, connected_at, balances?, error?}` |

### اعتبارسنجی

قبل از ذخیره، `get_balances(token)` صدا زده می‌شه:

- **200** → ذخیره + `wallex_connected_at=now`
- **401/403** → «توکن نامعتبر یا منقضی» — ذخیره نکن
- **Network/Timeout** → «الان نمی‌تونیم به والکس وصل شیم — بعداً امتحان کن»

اینطوری **هرگز** توکن معیوب ذخیره نمی‌شه.

### UX — صفحه‌ی /settings/wallex

**Disconnected:**
- عنوان: «اتصال به والکس»
- متن: «برای دیدن دارایی واقعی و (به‌زودی) معامله‌ی واقعی، توکن View حساب خودتو وارد کن.»
- لینک: «چطور توکن بسازم؟»
- input (type=password) + toggle نمایش
- دکمه: «اتصال و اعتبارسنجی»
- نشان امنیتی: «توکن رمزنگاری می‌شه و فقط برای خواندن استفاده می‌شه.»

**Connected:**
- «متصل ✅ — [تاریخ]»
- جدول موجودی‌های واقعی والکس
- دکمه: «قطع اتصال» (با confirm)

### فازبندی

**۱۷.۸.۱** — Fernet helper + key setup + WallexExchange override
**۱۷.۸.۲** — Backend: 3 endpoint + اعتبارسنجی + ۱۰ تست
**۱۷.۸.۳** — Frontend: `/settings/wallex` + hooks
**۱۷.۸.۴** — (بعداً) Trade token + سفارش واقعی

## Consequences

- **Positive:**
  - کاربر موجودی واقعی می‌بینه → اعتماد بیشتر
  - اتصال امن (Fernet) با کلید جدا از JWT
  - Paper state مستقل → کاربر بی‌محابا آزمایش می‌کنه
  - endpoint و UI آماده برای فاز ۱۷.۸.۴ (Trade)

- **Negative:**
  - اگه `WALLEX_TOKEN_ENC_KEY` گم شه → همه باید re-connect کنن
  - توکن View فقط خواندنه — کاربر باید برای معامله‌ی واقعی بعداً دوباره وصل کنه (با Trade token)

- **Neutral:**
  - `wallex_token_encrypted` و `wallex_connected_at` از فاز ۱۷ آماده‌ست
  - WallexExchange فقط پارامتر جدید می‌گیره

## References

- ADR 0015 — user paper state (paper مستقل)
- ADR 0016 — delimiter layering (برای نوشتن این سند)
- Migration `291b79050370` — ستون‌های `wallex_*` در `users`
- `app/infrastructure/exchange/wallex/client.py` — نیاز به override کوچیک
- `app/presentation/api/v1/user.py` — الگوی endpointهای user
- `app/core/auth.py` — JWT (کلید جدا از Fernet)
- AI_PRIMER v2.5 — M20-M25 (شاهد، dry-run، E2E با مرورگر، ...)

---

## Addendum — (جای خالی برای تصحیح‌های آینده)
