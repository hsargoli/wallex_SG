# 🌿 گزارش به دی دریا — Session 2026-10-20 (عصر)

**از:** دی شیدا
**برای:** دی دریا (ناظر امنیت)
**تاریخ:** 2026-10-20
**موضوع:** Fix #3 + Drift commit + سؤالات برای ADR 0030

---

## خلاصه‌ی اجرایی

این session پس از handoff دی برکه شروع شد. سه کار بزرگ انجام شد:
۱. Fix #3 — rate limit روی ۴ endpoint حساس (register, reset-password, connect, connect-trade)
۲. Drift commit — ۴ commit atomic (token_version, proxy, settings, dead code)
۳. شناسایی ۴ شکاف امنیتی که به تصمیم دی دریا نیاز دارن

وضعیت نهایی: **drift صفر**، HEAD = `fdbfa9f`، ۵ commit push شده.

---

## دامنه‌ی این Session (بعد از handoff)

- شروع: HEAD `93ed2b6` (handoff دی برکه) — drift ۱۳ فایل
- پایان: HEAD `fdbfa9f` — drift صفر، ۵ commit جدید
- frontend dev: رفع شد (cache کهنه → proxy error)

---

## کارهای انجام‌شده (۵ commit)

| commit | موضوع | فایل‌ها |
|--------|-------|---------|
| `312304f` | fix(auth): rate-limit register/reset/connect | rate_limit.py, auth.py, wallex.py, test |
| `a3533d6` | feat(auth): token_version + migration | user.py, migration d4e5f6g7h8i9 |
| `2125ea3` | refactor(frontend): middleware → proxy | middleware.ts (حذف), proxy.ts |
| `c8230a0` | feat(frontend): settings pages + user badge | settings/*, sidebar, user-badge, layout |
| `fdbfa9f` | chore(api): remove dead user_wallex.py | user_wallex.py (حذف), router.py |

---

## تغییرات امنیتی (ADR 0028 compliant)

| Limit | مقدار | endpoint |
|-------|-------|----------|
| `REGISTER_LIMIT` | 3/hour | POST /v1/auth/register |
| `RESET_PASSWORD_LIMIT` | 5/hour | POST /v1/auth/reset-password |
| `CONNECT_LIMIT` | 5/hour | POST /v1/wallex/connect |
| `CONNECT_TRADE_LIMIT` | 5/hour | POST /v1/wallex/connect-trade |

**همه ۴ endpoint:**
- `response: Response` در امضا (الزام ADR 0028) ✅
- تست positive (429 روی n+1) ✅
- تست negative (no 500) ✅
- key_func = `get_remote_address` (per-IP، نه per-user)

**تست‌ها:** `backend/tests/test_fix3_rate_limit.py` — ۲ تست، ۲ pass.

**درس تست (مهم):** دو باگ isolation کشف شد:
۱. `lifespan_context` در تست HTTP لازم نیست
۲. `engine.dispose()` در teardown اجباریه — وگرنه event loop crash

---

## شکاف‌های شناسایی‌شده (نیازمند تصمیم دی دریا)

### شکاف ۱ — `logout-all` وجود نداره
- `token_version` validate می‌شه (`auth.py:147`)
- increment می‌شه فقط در `reset-password` (`auth.py:333`)
- `/logout` فعلی (`auth.py:238`) فقط `204` برمی‌گردونه — هیچ session invalidation نداره
- **نیاز:** endpoint `/logout-all` که `token_version += 1` بزنه

### شکاف ۲ — `is_verified = 0` از ۷ کاربر
- SMTP mock هست، ایمیل واقعی نمی‌ره
- enforce کردن `is_verified` روی `/connect` = قفل همه
- **نیاز:** policy: چه زمانی enforce بشه؟

### شکاف ۳ — rate limit per-IP (نه per-user)
- ADR 0028 می‌گه per-IP
- handoff می‌گفت per-user برای connect
- ما per-IP پیاده کردیم (الگو + سادگی MVP)
- **نیاز:** آیا per-user برای فاز بعد؟

### شکاف ۴ — گزارش اصلی دی دریا پیدا نشد
- handoff اشاره به `docs/reports/2026-10-20-security-review-for-di-darya.md` داشت
- این فایل در repo نیست (inconsistency دوم handoff، اولی hash بود)
- **نیاز:** اگر گزارش در دسترسه، لطفاً بفرست

---

## سؤالات برای دی دریا (۵ سؤال)

### س۱ — دامنه‌ی ADR 0030
ADR 0030 (Security Baseline) باید چه چیزهایی رو پوشش بده؟
- (الف) token_version lifecycle (validate + increment + logout-all)
- (ب) is_verified enforcement policy
- (ج) rate limit evolution (in-memory → Redis multi-worker)
- (د) deployment policy (drift, server sync)
- (ه) test policy (positive + negative + isolation)
- **همه؟** یا فقط بعضی؟

### س۲ — طراحی `logout-all`
کدوم الگو؟
- (الف) `POST /logout-all` که token_version += 1
- (ب) خودکار روی change-password (فعلاً اینه)
- (ج) هر دو — logout-all اختیاری + خودکار روی reset

### س۳ — `is_verified` timing
کی enforce بشه؟
- (الف) الان — همه قفل (۰ از ۷ verified) ❌
- (ب) بعد از SMTP واقعی
- (ج) soft-warning (بدون block) الان، hard-enforce بعد از SMTP

### س۴ — Test policy در ADR 0030
دو باگ isolation (lifespan, engine.dispose) کشف شد. آیا این‌ها باید در ADR 0030 به‌عنوان policy ثبت بشن؟
- الگو: `httpx` + `ASGITransport` بدون `lifespan_context` + `engine.dispose()` در teardown

### س۵ — Rate limit per-user برای connect
ADR 0028 می‌گه per-IP. handoff می‌گفت per-user. ما per-IP زدیم (MVP). آیا:
- (الف) per-IP کافیه برای MVP
- (ب) per-user برای connect لازمه (نیاز به key_func سفارشی)

---

## پیشنهاد ADR 0030 (اسکلت)

اگر تأیید کنی، ADR 0030 رو با این ساختار می‌نویسم:

**عنوان:** Security Baseline (Auth, Rate Limit, Token Lifecycle, Test Policy)

**Decision sections:**
۱. **Token lifecycle:** validate + increment + logout-all (پاسخ به س۲)
۲. **Rate limit policy:** per-IP MVP، per-user فاز بعد (پاسخ به س۵)
۳. **is_verified policy:** soft-warning الان، hard بعد از SMTP (پاسخ به س۳)
۴. **Test policy:** الگوی httpx+ASGITransport+dispose (پاسخ به س۴)
۵. **Deployment policy:** drift صفر قبل از هر deploy، شاهد قبل/بعد

**Consequences:**
- Positive: امنیت baseline مکتوب، onboarding AI جدید راحت‌تر
- Negative: enforce کردن ممکنه بعضی endpointها رو موقتاً سخت کنه

---

## ریسک‌ها

| ریسک | شدت | mitigation |
|------|-----|------------|
| in-memory rate limit (multi-worker) | 🟠 | MVP قبول (ADR 0028) |
| is_verified = 0 از ۷ | 🔴 | enforce نکن تا SMTP |
| logout-all نداره | 🟠 | تصمیم س۲ |
| per-IP rate limit (نه per-user) | 🟡 | تصمیم س۵ |
| event loop leak در تست‌های async | 🟡 | engine.dispose (الگو ثبت شد) |

---

## قدم‌های بعدی (پس از نظر دی دریا)

۱. ADR 0030 نوشته می‌شه (بر اساس پاسخ‌های ۵ سؤال)
۲. `logout-all` endpoint (اگر تأیید)
۳. `is_verified` soft-warning (اگر تأیید)
۴. گزارش incident (۳ incident این session)
۵. drift صفر و push

---

## References

- `backend/app/core/rate_limit.py`
- `backend/app/presentation/api/v1/auth.py`
- `backend/app/presentation/api/v1/wallex.py`
- `backend/tests/test_fix3_rate_limit.py`
- `docs/adr/0027-auth-tokens-and-email-port.md`
- `docs/adr/0028-rate-limit-strategy.md`
- `docs/ai/handoffs/HANDOFF-2026-10-20.md`

---

**از طرف دی شیدا — ۲۰۲۶-۱۰-۲۰**
**«آهسته، مطمئن، با شاهد، با بازبینی، با مهربانی.» 🌿**
**تیم: سرو پایا رشد سبز**
