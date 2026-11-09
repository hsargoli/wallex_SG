# ADR-0039 — SarvRouter as Copilot (Advisory, Not Autonomous)

- **Status:** Proposed
- **Date:** 2026-11-09
- **Author:** دی دریا (CTO)
- **Reviewers:** حسین (رهبر), دی کویر (مسئول SarvRouter)
- **Supersedes:** —
- **Related:** ADR-0035 (SarvRouter Builder MVP), ADR-0037 (HumanSignal), ADR-0038 (bear_hunter cleanup)

---

## 1. Context

تا پیش از این تاریخ، SarvRouter به عنوان یک *orchestrator خودمختار* در حال ساخت بود:
با `start_bot`/`stop_bot`/`stop_all` واقعی، چک خودکار `daily_loss_limit`، و در صورت لزوم
`kill_switch_auto = True`.

بر اساس تصمیم ۲۰۲۶-۱۱-۰۹، مسیر اکوسیستم به سمت **Copilot** تغییر میکند:
همه‌ی تصمیم‌های نهایی توسط کاربر گرفته میشود، و سیستم فقط **پیشنهاد** میدهد.

بررسی SarvRouter (گزارش دی دریا، نسخه ۱.۰، ۲۰۲۶-۱۱-۰۹) نشان داد که:

- منطق چرخش رژیم (`regime`, `stability_window`, `cooldown`, `hydrate_from_state`)
  از نظر منطقی بالغ است.
- اما `scheduler.py` ربات‌ها را با no-op صدا می‌زند (F9) — که در چارچوب خودمختار باگ بود،
  ولی در چارچوب Copilot **تأیید طراحی** است.
- `daily_pnl_pct` در `store.py` هیچ write site ندارد (F10) — یعنی لایه‌ی ۳ عملاً dead code است.
- در `bot.py:65-66` خود SarvRouter تصمیم `kill_switch_auto=True` می‌گیرد (F14) —
  این دقیقاً خلاف روح Copilot است.

## 2. Decision

**SarvRouter از این پس یک Copilot است — نه یک ربات خودمختار.**

از این تصمیم سه پیامد مستقیم می‌آید:

### 2.1. SarvRouter هیچ اجرایی انجام نمی‌دهد

- `start_bot` / `stop_bot` / `stop_all` در چارچوب Copilot **no-op** می‌مانند.
- هیچ auto-mutation روی state کاربر (از جمله `kill_switch_auto`) مجاز نیست.
- تشخیص (detect) از تصمیم (decide) از اجرا (execute) **جدا** می‌شوند:
  - SarvRouter فقط تشخیص و پیشنهاد می‌دهد.
  - کاربر تصمیم می‌گیرد.
  - اجرا در لایه‌ای خارج از SarvRouter (کاربر یا UI) اتفاق می‌افتد.

### 2.2. `gate` از «کنترل» به «پیشنهاد» تغییر می‌کند

- `gate.json` همچنان نوشته و خوانده می‌شود، ولی مصرف‌کننده‌اش فقط **UI** است
  که به کاربر نشان می‌دهد «SarvRouter پیشنهاد می‌دهد که ورود جدید مجاز نباشد».
- هیچ ربات Live (از جمله Nooaah) نباید به `gate.json` به عنوان اجرا تکیه کند.
  (Nooaah خارج از محدوده‌ی این ADR است؛ فقط اثر متقابل، در بخش Open Questions.)
- رفتار fail-open فعلی `read_gate` (بازگشت `allow_new_entries=True` در صورت خرابی)
  با فلسفه‌ی Copilot سازگار است: چون gate فقط پیشنهاد است، خرابی‌اش نباید مانع شود.

### 2.3. پنج فاز بهبود Copilot

مسیر SarvRouter به سمت Copilot در پنج فاز تعریف می‌شود. ترتیب وابستگی‌محور است:

| فاز | نام | تحویل | پیش‌نیاز |
|---|---|---|---|
| ۱ | بامعنا | هر tick یک `DecisionReason` با دلیل + شاهد برمی‌گرداند | — |
| ۲ | ریسک | برچسب ریسک (fee + slip + spread) روی هر پیشنهاد | فاز ۱ |
| ۳ | گفتگو | endpoint `POST /copilot/why?tick_id=` با پاسخ ساختاریافته (rule-based) | فاز ۱ |
| ۴ | بازخورد | جدول `copilot_feedback` + قاعده‌ی حداقل نمونه | فاز ۱، ۲ |
| ۵ | چندسناریو | ۲–۳ گزینه با trade-off در هر tick | فاز ۱، ۲ |

ترتیب اجرا: **۱ → ۲ → (۳ و ۵ موازی) → ۴**.

**فاز ۳ ابتدا rule-based است** (نه LLM). LLM فقط به عنوان لایه‌ی دوم روی همان
`evidence` سوار می‌شود — تا اگر LLM در دسترس نبود، گفتگو نمیرد.

## 3. Consequences

### 3.1. یافته‌های قبلی که بازتعریف می‌شوند

| یافته | فریم قبل | فریم جدید |
|---|---|---|
| F9 (no-op lambdas) | باگ بحرانی | ✅ تأیید طراحی — باید در ADR-0040 مستند شود |
| F10 (`daily_pnl_pct` بیتغییر) | dead code | 🟠 پیشنهاد بی‌مبنا — فاز ۱ باید منبع را تعریف کند |
| F11 (`user_id` هاردکد) | per-user شکسته | 🔴 همچنان بحرانی — پیشنهاد به کاربر اشتباه، ضرر است |
| F12 (gate fail-open) | ایمنی معکوس | 🟢 بی‌خطر — gate فقط پیشنهاد است |
| F14 (`kill_switch_auto` خودکار) | — | 🔴 **نقض Copilot** — باید به «تشخیص + پیشنهاد» تغییر کند |

### 3.2. قانون ۱۸ (۵ لایه) برای Copilot

قانون ۱۸ در پرایمر برای ربات‌های **خودمختار** تعریف شده است. برای Copilot، این قانون
به شکل زیر بازتفسیر می‌شود:

- لایه ۱ (`is_trading_enabled`): همچنان لازم — Copilot نباید برای کاربر غیرفعال پیشنهاد دهد.
- لایه ۲ (`live_stage`): همچنان لازم — پیشنهاد در stage 0/1 با برچسب «شبیه‌سازی» نمایش داده شود.
- لایه ۳ (`daily_loss_limit`): **به «propose» تغییر می‌کند** — پیشنهاد توقف، بدون اجرا.
- لایه ۴ (`kill_switch`): فقط **manual** — `kill_switch_auto` حذف می‌شود (F14).
- لایه ۵ (`audit per-user`): همچنان لازم — هر پیشنهاد ثبت می‌شود، حتی اگر کاربر رد کند.

### 3.3. تصمیم‌های صریحاً خارج از محدوده

- Nooaah، bear_hunter، scalp_master و هر ربات خودمختار ساخته‌شده **بسته** هستند.
  تغییر رفتاری در آن‌ها انجام نمی‌شود.
- تنها اثر متقابل، از طریق `gate.json` است — که در بخش Open Questions بررسی می‌شود.

## 4. Open Questions

این سؤالات **پاسخ ندارند** و باید قبل از Accepted شدن ADR پاسخ بگیرند:

1. **محدوده‌ی Copilot:** آیا Nooaah (که Live است) هم در آینده به Copilot تبدیل می‌شود،
   یا دو استاندارد جدا (SarvRouter = Copilot، Nooaah = autonomous-with-5-layers) حفظ می‌شود؟
2. **gate و Nooaah:** آیا `gate.json` همچنان توسط Nooaah خوانده می‌شود؟ اگر بله،
   چگونه «پیشنهاد» از «اجرا» تفکیک می‌شود؟
3. **منبع `daily_pnl_pct`:** مقدار این فیلد از کجا می‌آید؟ آیا درصد است یا کسری؟
4. **UI:** SarvRouter الان در UI کجا دیده می‌شود؟ (route، کامپوننت، فیلدهای نمایش‌داده‌شده)
   این برای طراحی فاز ۱ حیاتی است.
5. **`expires_at` (R26):** معنای دقیقش چیست؟ Copilot باید بداند تا «پیشنهاد منقضی» را
   درست مدیریت کند.

## 5. Implementation Plan

- **قبل از هر کد:** این ADR به Accepted تغییر وضعیت دهد (تأیید حسین + دی کویر).
- **قبل از فاز ۱:** ADR-0040 (Copilot Decision Contract) نوشته و Accepted شود.
- **فاز ۱:** `DecisionReason` (dataclass) + بازگشت سازگار با dict فعلی + تست‌های جدید.
- **فاز ۲ تا ۵:** هر فاز یک ADR کوچک یا یک Addendum، طبق M11.

**هیچ کدی قبل از Accepted شدن ADR-0039 و ADR-0040 نوشته نمی‌شود.**

---

## 6. Witness

- گزارش SarvRouter Audit v1.0 — `docs/di_darya/SARVROUTER_AUDIT_REPORT.md`
- خروجی grep، cat و wc — ۲۰۲۶-۱۱-۰۹
- فایل‌های مرجع: `scheduler.py`, `bot.py`, `gate.py`, `store.py`
- ADRهای مرتبط: 0035، 0037، 0038

---

## Addendum 1.1 — Gate Reality Correction (2026-11-09)

**Status:** Part of ADR-0039 v1.1
**Trigger:** شاهد جدید پس از Proposed شدن v1.0 نشان داد بخش 2.2 با کد تناقض دارد.
**Approach:** M27 — Addendum برای تصحیح، نه ADR جدید.

### A1.1.1. شاهد جدید

سه یافته که ادعای «gate فقط برای UI است» را رد میکند:

**F15 — gate واقعاً Nooaah را کنترل میکند.**
- `nooaah/scheduler.py:82`:
  `result = await runner.run_cycle(entries_allowed=gate.allow_new_entries)`
- یعنی مقدار نوشته‌شده در `bot.py:93` مستقیماً به ورودی Nooaah می‌رود.
- این یک **کانال کنترل** است، نه advisory.

**F16 — UI فعلی Copilot را نشان نمیدهد.**
- `frontend/app/(app)/sarvrouter/page.tsx:18-20`:
  فقط `useSarvRouterStatus`, `useSarvRouterKill`, `useSarvRouterReenable`.
- هیچ‌جای UI: `reason`, `evidence`, `alternatives`, `tick_id`.
- `frontend/app/(public)/learn/page.tsx:66`: «SarvRouter در Paper Mode ۲۴/۷ کار می‌کند» — یعنی UI عمومی هم SarvRouter را autonomous معرفی می‌کند.

**F17 — gate سراسری است، per-user نیست.**
- `gate.py`: `write_gate` هیچ پارامتر `user_id` ندارد. یک فایل `gate.json` واحد.
- رژیمِ یک user SarvRouter (`production-default`)، ورودِ همه‌ی کاربران Nooaah را تعیین میکند.

### A1.1.2. تصحیح بخش 2.2

**متن قبلی (v1.0، اکنون باطل):**
> «gate.json همچنان نوشته و خوانده میشود، ولی مصرفکنندهاش فقط UI است»

**متن جایگزین (v1.1):**

gate.json در وضعیت فعلی یک **کانال کنترل از SarvRouter به Nooaah** است
(F15). این با فلسفه‌ی Copilot در تناقض است. برای رفع تدریجی این تناقض،
**گزینه B** انتخاب میشود:

- `allow_new_entries` با همان منطق فعلی (`regime == Regime.UPTREND`) نوشته میشود.
  Nooaah دقیقاً مثل امروز رفتار میکند — **هیچ تغییر رفتاری اعمال نمیشود.**
- یک فیلد جدید `proposed_allow_new_entries` به `GateState` اضافه میشود،
  که همان مقدار `allow_new_entries` را آینه میکند.
- UI (فاز ۱ Copilot) از این پس `proposed_allow_new_entries` را بهعنوان
  «پیشنهاد SarvRouter» نشان میدهد، در حالی که `allow_new_entries` بهعنوان
  «کنترل فعلی» در سایه باقی میماند.
- `read_gate` در Nooaah **تغییر نمیکند** (خارج از محدوده).

### A1.1.3. بدهی فنی ثبتشده

این Addendum یک تناقض را **مستند** میکند، نه حل. بدهی زیر رسمی میشود:

| # | بدهی | تاریخ بازبینی | مالک |
|---|---|---|---|
| D-Gate-1 | `allow_new_entries` هنوز Nooaah را کنترل میکند | ۲۰۲۷-۰۲-۰۹ (۳ ماه) | دی کویر + دی دریا |
| D-Gate-2 | gate سراسری است، per-user نیست (F17) | ۲۰۲۷-۰۲-۰۹ | دی کویر |
| D-Gate-3 | UI عمومی (learn/page.tsx:66) SarvRouter را autonomous معرفی میکند | قبل از فاز ۳ | دی فردوس (فرانت) |
| D-Gate-4 | `nooaah/scheduler.py:80-82` در محدوده نیست ولی اثرگذار است | ۲۰۲۷-۰۲-۰۹ | حسین (تصمیم) |

**شرط بازبینی:** اگر تا ۲۰۲۷-۰۲-۰۹ تصمیم به گزینه A یا C گرفته نشد، این بدهی به ADR-0041 ارتقا مییابد.

### A1.1.4. آنچه در ADR-0039 v1.1 بدون تغییر میماند

- بخش 1 (Context) ✅
- بخش 2.1 (هیچ اجرایی) ✅
- بخش 2.3 (پنج فاز) ✅
- بخش 3.1 (بازتعریف F9/F10/F11/F12/F14) ✅
- بخش 3.2 (بازتفسیر قانون ۱۸) ✅
- بخش 3.3 (Nooaah خارج از محدوده) ✅
- بخش 4 (Open Questions) — سؤال ۲ (gate) پاسخ گرفت → بخش A1.1.2 جایگزین.

### A1.1.5. Witness

- خروجی grep و sed — ۲۰۲۶-۱۱-۰۹
- فایل‌ها: `nooaah/scheduler.py:80-82`, `sarv_router/gate.py`, `sarv_router/bot.py:93`, `sarvrouter/page.tsx:18-20`, `learn/page.tsx:66`
