# ADR-0002: Archive SarvTiger Analyzer — No Standalone Edge

**تاریخ:** 2026-10-30
**وضعیت:** Accepted
**نویسنده:** دی رود
**بازبین:** دی کویر

## Context

sarv_tiger (BB Squeeze، PF=1.14) برای تقویت edge، یک لایه‌ی analyzer
(Historical Pattern Matching) دریافت کرد: features → similarity → outcome.

هدف: آیا «حافظه‌ی الگو» می‌تواند edge مستقل تولید کند؟

## Decision

**Analyzer آرشیو می‌شود.** کد در `analyzer/` می‌ماند (۵۵ تست GREEN)،
ولی در production استفاده نمی‌شود.

## Evidence (شاهد)

Full backtest روی ۱۱,۰۷۳ پنجره (۴.۵ سال BTC 4h):

| mode | TP | train PF | test PF | WF-2 (نزول) |
|---|---|---|---|---|
| alpha | 8 | — | 0.45 | — |
| delta | 8 | 1.05 | 0.85 | 0.26 |
| gamma | 8 | 1.06 | 0.78 | 0.49 |
| delta | 2 | 0.92 | 0.56 | — |
| gamma | 2 | 1.03 | 0.90 | — |

**هیچ ترکیبی PF>1.0 در test نداد.** WF-2 (نزول) همه را نابود کرد.

## Root Cause

1. **Horizon mismatch:** analyzer جهت ۱۶۸h را پیش‌بینی می‌کند، exit در ۲۴h-۱۶۸h
2. **Asymmetric R/R:** TP=8ATR به‌ندرت می‌رسد → time-exit غالب
3. **Regime concentration:** edge فقط در صعودی (WF-1, WF-3)، در نزول بدتر از random

## Consequences

**مثبت:**
- ۵M سرمایه از ضرر نجات یافت (PF<1 در test = ضرر انتظاری)
- ۵۵ تست GREEN به‌عنوان مرجع باقی می‌ماند
- AP-39, AP-40, AP-41 ثبت شد

**منفی:**
- ۷ ساعت کار روی analyzer، edge تولید نکرد
- sarv_tiger بدون analyzer می‌ماند (PF=1.14 نازک)

**خنثی:**
- sarv_tiger فعلی: paper mode ۲ هفته (تصمیم جدا)
- تمرکز روی SarvRouter + nooaah

## Alternatives Considered

1. **regime filter (گزینه B):** analyzer فقط در UPTREND + BB Squeeze AND
   - رد شد: coupling با SarvRouter، و analyzer در UPTREND هم test PF<1
2. **TP tuning (TP=2.5, 3):** رد شد (AP-28، p-hacking)
3. **آرشیو (این ADR):** پذیرفته شد

## Broader Lesson (فراتر از analyzer)

این شکست، فقط درباره‌ی analyzer نیست. سه مشکل ساختاری در `sarv_tiger` را آشکار کرد:

1. **Horizon mismatch:** استراتژی که ادعای swing دارد، در exit مثل scalping عمل می‌کند (TP=8ATR در 24-168h).

2. **Regime dependence:** هر استراتژی long-only (که TP=8ATR دارد) در نزول، ضرر می‌دهد — مگر اینکه gate (مثل SarvRouter) در نزول بسته شود.

3. **WR vs PF:** WR=۲۰٪ با TP=8ATR، PF=۱.۱۴ می‌دهد. با TP=2ATR، WR=۴۰٪ ولی PF=۰.۹۰. **هیچ‌کدام کافی نیست.**

**نتیجه:** sarv_tiger فعلی (PF=۱.۱۴) هم edge نازکی دارد. paper mode ۲ هفته، ولی با انتظار سود کم، نه سود کلان.

## Lessons (برای پرایمر)

- **AP-39:** گزارش منفی، یک پیروزی است
- **AP-40:** WR بالا + PF پایین = بردهای کوچک، lossهای بزرگ‌تر
- **AP-41:** argparse choices را همزمان با mode جدید آپدیت کن
