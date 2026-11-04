# ADR 0035 — SarvRouter Builder (Interactive Config)

- **تاریخ:** 2026-11-04
- **وضعیت:** Proposed (MVP 1-2 روز)
- **نویسنده:** دی باران (ایده از حسین)
- **شاهدان:** Investigate ML (۴ تست FAIL) + Copilot finalization

## Context

### چه شد که به این تصمیم رسیدیم؟

۱. **ML جهت‌دهی، fail شد:** ۴ تست ML (13, 14) — همه FAIL. پیش‌بینی جهت با داده‌ی تکنیکال ممکن نیست.

۲. **SarvRouter فعلی، یک config ثابت دارد:** `uptrend_adx_min=25, ema_period=50, stability_window=36`. کاربر نمی‌تواند ببیند «اگر ADX=30 باشد چه می‌شود؟».

۳. **ایده‌ی حسین:** «کاربر باید بتواند SarvRouter را با گزینه‌های خودش بسازد و تست کند. مثل یک بازی.»

## Decision

**SarvRouter Builder (Copilot):**

- **Frontend:** صفحه‌ی `/research/sarvrouter-builder` با فرم پارامترها.
- **Backend:** endpoint `POST /v1/sarvrouter/backtest` (config → verdict).
- **Data flow:** کاربر پارامتر → اجرای backtest روی داده‌ی تاریخی → برگشت accuracy + forward returns + trades.

### پارامترهای قابل تنظیم (MVP)

| پارامتر | پیش‌فرض | محدوده |
|---|---|---|
| `uptrend_adx_min` | 25 | 15-40 |
| `downtrend_adx_min` | 25 | 15-40 |
| `range_adx_max` | 20 | 10-30 |
| `ema_period` | 50 | 20-200 |
| `stability_window` | 36 | 6-100 |
| `cooldown_candles` | 12 | 3-50 |

### خروجی

| متریک | توضیح |
|---|---|
| **Accuracy** | دقت کل (up/down/range) |
| **Per-regime accuracy** | uptrend, downtrend, range |
| **Forward returns** | میانگین 24h, 7d |
| **Trades** | تعداد switch |
| **Badge** | «بهتر از default؟» |

### «بازی»:

- کاربر پارامترها را عوض می‌کند → دکمه‌ی «Run» → نتیجه می‌بیند.
- دکمه‌ی «Copy as URL» — تا config را با دیگران share کند.
- Leaderboard: بهترین accuracy (اختیاری، فاز ۲).

## Consequences

### مثبت:
- ✅ Copilot واقعی: کاربر می‌سازد، می‌بیند، یاد می‌گیرد.
- ✅ engagement: «مثل بازی» — کاربر هی تست می‌کند.
- ✅ شفافیت: SarvRouter یک جعبه‌سیاه نیست.

### منفی / ریسک:
- 🟡 Backend compute: هر اجرا، ۵۱K کندل (اما ~۱-۲s، قابل قبول).
- 🟡 UI complexity: form + run + results.
- 🟡 Cache: نتایج تکراری (config مشابه) را cache کنیم.

### MVP scope (1-2 روز):
- فقط ۶ پارامتر.
- فقط یک symbol (BTCUSDT).
- فقط accuracy + per-regime.
- بدون leaderboard، بدون share (فاز ۲).

## منابع:
- ADR-0034 (SarvBots = Analysis Platform)
- صفحه‌ی regime-accuracy (موجود)
- Investigate ML (۴ تست FAIL)
