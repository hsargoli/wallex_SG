# گزارش ممیزی پروژه — امنیت، تمیزی گیت، تمیزی کد

**تاریخ (میلادی):** 2026-10-02
**ساعت (میلادی):** 15:43
**تاریخ (شمسی):** 1405/07/10
**ساعت (شمسی):** 15:43
**مدت:** حدود ۴–۵ ساعت کار فشرده
**وضعیت:** کامل — ۳ مرحله از ۶ مرحله ممیزی انجام شد

---

## 🎯 چرا این ممیزی؟

قبل از اضافه کردن قابلیت‌های جدید به پروژه، تصمیم گرفتیم پایه‌ها را محکم کنیم:
- امنیت کلیدها و رمزها
- تمیزی مخزن گیت
- کیفیت کد (lint و type checking)

هدف: پایه‌ای تمیز که اضافه کردن قابلیت‌های بعدی روی آن، سریع و بی‌دردسر باشه.

---

## 🔒 مرحله ۱: امنیت

### مشکل اصلی که پیدا شد

فایل `dox.xml` (یادداشت شخصی) شامل **API Key واقعی والکس** بود:

WALLEX_API_KEY="<کلید واقعی در والکس>"
text


### کارهای انجام شده

| # | کار | نتیجه |
|---|-----|-------|
| 1 | Revoke API Key قدیمی در پنل والکس | ✅ انجام شد |
| 2 | چک تاریخچه گیت برای کلید | ✅ هیچ‌وقت کامیت نشده بود |
| 3 | بهبود `.env.example` | ✅ placeholder واضح + راهنمای فارسی |
| 4 | محدود کردن دسترسی `.env` به ۶۰۰ | ✅ فقط owner |
| 5 | حذف `dox.xml` از گیت tracking | ✅ تو گیت نمیره، ولی روی دیسک می‌مونه |
| 6 | تقویت `.gitignore` | ✅ ۲۶ خط جدید (pem, key, secrets, ...) |
| 7 | چک `git log` برای الگوهای حساس | ✅ هیچی پیدا نشد |

### یادداشت

`dox.xml` فایل شخصیه و از این به بعد کاملاً دست نخورده می‌مونه — فقط تو گیت track نمیشه.

---

## 🧹 مرحله ۲: تمیزی گیت

### مشکلاتی که پیدا شد

| # | مشکل | راه‌حل |
|---|------|-------|
| 1 | فایل شبح با newline در نام | ✅ حذف با git update-index |
| 2 | ۲۱ فایل `.bak` تو دیسک | ✅ همه حذف شدن |
| 3 | runtime data تو گیت | ✅ از tracking حذف، تو دیسک موند |
| 4 | bundle backup | ✅ حذف شد |
| 5 | `.env.example.bak` | ✅ حذف شد |
| 6 | `test_dispatcher_load.py` تو روت | ✅ حذف شد |
| 7 | backup فایل index گیت | ✅ حذف شد |

### runtime data که از گیت حذف شد

- `backend/data/paper_trading/state.json`
- `backend/data/paper_v2/state.json`
- `backend/data/replay/state.json`
- `backend/data/replay/trades.jsonl`

این فایل‌ها به `.gitignore` اضافه شدن ولی رو دیسک باقی موندن.

### نکته فنی

فایل شبح یه مشکل عجیب بود — نامش شامل یه کاراکتر **newline واقعی (0x0A)** بود که با `git rm` معمولی قابل حذف نبود. با `git update-index --index-info` و ورودی byte-level حل شد.

---

## 🎨 مرحله ۳: تمیزی کد

### Backend (Python)

| ابزار | نتیجه قبل | نتیجه بعد |
|-------|-----------|-----------|
| `ruff check F401,F841` | ۳ خطا | ✅ 0 errors |

**تغییرات:**
- `bot_simulator.py`: حذف `Dict`, `Any` از import
- `bot_simulator.py`: حذف متغیر بی‌استفاده `c`

### Frontend (TypeScript + ESLint)

**ESLint 9 راه‌اندازی شد** (چون `next lint` در Next.js 16 منسوخ شده):
- `eslint@9`
- `@eslint/js@9`
- `typescript-eslint@8`
- `eslint-plugin-react@7`
- `eslint-plugin-react-hooks@5`
- `eslint.config.mjs` سازگار با Next.js 16

**۸ فایل تمیز شد:**

| # | فایل | مشکل |
|---|------|------|
| 1 | `app/bots/[slug]/page.tsx` | `CardDescription` بی‌استفاده |
| 2 | `app/bots/page.tsx` | `Play`, `Target` بی‌استفاده |
| 3 | `app/markets/[symbol]/chart/page.tsx` | `formatNumber` بی‌استفاده |
| 4 | `app/paper-trading/page.tsx` | `CompareResultItem` بی‌استفاده |
| 5 | `app/signals/[symbol]/page.tsx` | `SignalType`, `formatNumber`, `useRouter`, `router` |
| 6 | `components/markets/symbol-switcher.tsx` | `cn` بی‌استفاده |
| 7 | `components/signals/levels-panel.tsx` | `formatNumber`, prop `current` بی‌استفاده |
| 8 | `components/signals/signals-chart.tsx` | hook dependency (`isEnabled`) |

### نتیجه نهایی

| ابزار | نتیجه |
|-------|-------|
| `ruff` | ✅ 0 errors, 0 warnings |
| `tsc --noEmit` | ✅ 0 errors |
| `npx eslint .` | ✅ 0 problems |

---

## 📊 کامیت‌های امروز (۹ کامیت)

656df72 chore(lint): fix all ESLint warnings and unused variables
0bc56c4 chore(lint): setup ESLint 9 and cleanup backend imports
66117b3 chore: finalize gitignore updates and remove last .bak file
2abc71b chore: cleanup runtime data and backup files from git
0f53f6c chore(git): remove invalid index entry with newline path
1e3b18c chore: cleanup root directory
8c4e06d security: remove dox.xml from tracking, strengthen gitignore
8ec0666 chore(env): improve .env.example with security guidelines
0d66ee3 docs(reports): add simulator development report (2026-10-02)
text


---

## 💡 درس‌های آموخته

1. **API Key در فایل یادداشت شخصی = فاجعه.** هرگز کلید واقعی رو تو فایل‌های غیرمرتبط نذار. اگه چیزی شد، فوراً revoke کن.

2. **regex برای کد خطرناکه.** تلاش کردیم با regex importهای بی‌استفاده رو حذف کنیم، ولی importها ناقص شدن. راه درست: یکی‌یکی، با تأیید lint بعد از هر تغییر.

3. **git نمی‌تونه با نام‌های عجیب راحت کار کنه.** فایل با newline در نام، فقط با `git update-index --index-info` با byte-level ورودی قابل حذف بود.

4. **ESLint در Next.js 15+ تغییر کرده.** `next lint` منسوخ شده و باید مستقیم ESLint 9 با config جدید استفاده کرد.

5. **همیشه بکاپ قبل از پاکسازی.** برای هر فایل مهم، `.bak` ساختیم و بعد با اطمینان پاک کردیم.

---

## 📌 وضعیت پروژه بعد از این ممیزی

| مرحله | وضعیت |
|-------|-------|
| ۱. امنیت | ✅ کامل |
| ۲. تمیزی گیت | ✅ کامل |
| ۳. تمیزی کد | ✅ کامل |
| ۴. ساختار پوشه‌ها | ⏳ بعدی |
| ۵. مستندات | ⏳ |
| ۶. تست‌ها | ⏳ |

---

## 🎯 قدم بعدی (مرحله ۴)

**بررسی ساختار پوشه‌ها:**
- یکنواختی نام‌گذاری (`snake_case` / `camelCase`)
- جداسازی منطق مشترک
- ساختار `services/`, `domain/`, `infrastructure/`
- جستجوی کد تکراری

**بررسی مستندات (مرحله ۵):**
- README اصلی
- مستندات API (auto-generated از FastAPI)
- راهنمای setup

**بررسی تست‌ها (مرحله ۶):**
- الان ۶ تست کوچیک هست
- اضافه کردن تست برای `bot_simulator` و Adapters

---

## 📎 فایل‌های مرتبط

- گزارش توسعه شبیه‌ساز: `docs/reports/2026-10-02_Simulator_Development.md`
- گزارش ممیزی (همین فایل): `docs/reports/2026-10-02_Project_Audit.md`

---

**پایان گزارش — نسخه ۱.۰**
