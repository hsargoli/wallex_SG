# ADR-0043 — Feedback Collection (MVP Scope)

- **Status:** Proposed
- **Date:** 2026-11-09
- **Author:** دی دریا (CTO)
- **Reviewers:** حسین (رهبر), دی کویر (مسئول SarvRouter)
- **Related:** ADR-0039 (Copilot), ADR-0040 (Decision Contract), ADR-0042 (Conversation MVP)

---

## 1. Context

فاز ۳ (گفتگو MVP) کامل شد: کاربر می‌تواند بپرسد «چرا؟» و پاسخ بگیرد.
فاز ۴ (یادگیری از بازخورد) قرار است کاربر بتواند بگوید «قبول دارم» یا «رد می‌کنم».

**شاهد از کد (۲۰۲۶-۱۱-۰۹):**
- هیچ مکانیزم feedback در SarvRouter وجود ندارد (`grep -i feedback` خالی).
- `AuditTrail` الگوی append-only JSONL را در `data/sarv_router/users/{user}.audit.jsonl` دارد.
- UI فعلی `/sarvrouter` فقط دکمه «چرا؟» دارد.

**نسخه کامل این فاز (Out of Scope):**
- تجمیع بازخورد و تنظیم `confidence`.
- یادگیری از الگوهای رد/قبول (در MVP نه).
- پرسش‌های چندگانه از کاربر.

## 2. Decision (MVP Scope)

فقط **جمع‌آوری** بازخورد. نه تحلیل. نه یادگیری. این یک بستر ساده است که در فازهای بعدی می‌توان روی آن ساخت.

### 2.1. محدوده MVP (In Scope)

- یک endpoint جدید: `POST /sarvrouter/feedback`
- بدنه: `{ "tick_id": str, "user_choice": "accept" | "reject" }`
- ذخیره در `data/sarv_router/users/{user}.feedback.jsonl` (الگوی `AuditTrail`).
- در UI: دو دکمه «تایید» و «رد» زیر کارت آخرین تصمیم.
- فقط برای **آخرین** تصمیم. اگر `tick_id` با `last_decision.tick_id` نخواند، پاسخ `409 Conflict`.

### 2.2. خارج از محدوده MVP (Future)

- تجمیع بازخورد (مثلاً «۷۰٪ قبول این هفته»).
- استفاده از بازخورد در `confidence` یا `SarvRouterConfig`.
- ثبت بازخورد برای تصمیم‌های تاریخی (بدون نیاز به `tick_id`).
- ثبت دلیل رد (مثلاً «سود کم بود»).

### 2.3. چرا فقط برای آخرین تصمیم؟

- MVP: ساده‌ترین حالت. کاربر فقط به پیشنهاد فعلی پاسخ می‌دهد.
- از تکرار بازخورد برای یک `tick_id` جلوگیری می‌کند (بازخورد قابل تکرار نیست).
- در فاز کامل، اگر نیاز شد، `tick_id` را در URL می‌گذاریم و هر tick را مستقل ثبت می‌کنیم.

### 2.4. ساختار FeedbackEntry (الگوی AuditEntry)

    @dataclass
    class FeedbackEntry:
        tick_id: str
        action: str            # از last_decision (برای context)
        user_choice: str       # "accept" | "reject"
        timestamp: str

## 3. Consequences

- **مزایا:** MVP سریع. یک JSONL جدید، یک endpoint، دو دکمه. هیچ تغییر schema در DB.
- **معایب:** هنوز یادگیری از بازخورد در رفتار SarvRouter اثر ندارد — فقط ثبت می‌شود.
- **تغییرات کد:**
  - `app/services/bots/sarv_router/feedback.py` (جدید)
  - `app/presentation/api/v1/sarvrouter.py` (endpoint جدید)
  - `frontend/app/(app)/sarvrouter/page.tsx` (دو دکمه)

## 4. Open Questions

۱. آیا `user_id` در URL یا Header بیاید؟
   - **تصمیم MVP:** ثابت `production-default` مثل بقیه. در آینده per-user.

۲. اگر کاربر دوباره feedback دهد (مثلاً اول accept کرد، بعد reject)؟
   - **تصمیم MVP:** هر دو در JSONL ثبت می‌شوند. تحلیل، کار فاز بعد.

۳. آیا باید در UI نمایش داده شود که «قبلاً بازخورد داده‌اید»؟
   - **تصمیم MVP:** بله، دکمه‌ها غیرفعال می‌شوند بعد از ثبت. با `refetch` بعدی، UI از `last_decision.tick_id` می‌فهمد که همین tick قبلاً feedback گرفته.

## 5. Witness

پذیرش با این شاهدها:
- ۵ تست جدید برای `FeedbackTrail` (write, read, serialize).
- ۳ تست برای endpoint (`accept`, `reject`, `409 on mismatch`).
- 1 تست UI (دکمه‌ها وجود دارند در page.tsx).
