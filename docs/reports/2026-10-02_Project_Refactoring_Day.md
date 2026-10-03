# گزارش جامع روز بازسازی پروژه

**تاریخ (میلادی):** 2026-10-02
**تاریخ (شمسی):** 1405/07/10
**مدت کار:** ~۷ ساعت فشرده
**تعداد کامیت:** ۲۲

---

## خلاصه‌ی یک‌خطی

پروژه از یک وضعیت آشفته (API Key لو رفته، ۳۱ تست فیل، مستندات ناقص) به یک پایه‌ی محکم (امن، تمیز، ۷۶ تست پاس، ۴۹۰۰ خط مستندات) تبدیل شد.

---

## اهداف روز

پیش از این روز، پروژه در وضعیت زیر بود:

- ⚠️ یک API Key والکس در فایل یادداشت شخصی لو رفته بود
- ⚠️ README می‌گفت «۷۶ تست، ۱۰۰٪ پاس» ولی ۳۱ تست فیل بودند
- ⚠️ main.py فقط ۳ router از ۱۴ رو mount می‌کرد
- ⚠️ scripts/ml/ شامل ۵۸ فایل بدون ساختار بود
- ⚠️ ۲۱ فایل .bak، runtime data در گیت، و فایل شبح با newline در نام
- ⚠️ مستندات تقریباً وجود نداشت (فقط ۱۸ خط docs/README)

**هدف:** ساختن پایه‌ی محکم قبل از ادامه‌ی Milestone 7

---

## تایم‌لاین کارها

### مرحله ۱: امنیت (~۳۰ دقیقه)

**کشف مشکل:**
- فایل `dox.xml` (یادداشت شخصی) شامل API Key واقعی والکس بود
- کلید در working directory بود ولی هرگز کامیت نشده بود
- ریسک: هر لحظه ممکن بود اشتباهاً کامیت شود

**اقدامات:**
1. ✅ Revoke API Key قدیمی در پنل والکس
2. ✅ بهبود `.env.example` با راهنمای فارسی
3. ✅ محدود کردن دسترسی `.env` به 600
4. ✅ حذف `dox.xml` از git tracking (ولی حفظ روی دیسک)
5. ✅ تقویت `.gitignore` با ۲۶ خط جدید
6. ✅ تأیید: کلید در تاریخچه گیت نیست

**نتیجه:** امنیت کامل ✅

---

### مرحله ۲: تمیزی گیت (~۴۵ دقیقه)

**مشکلات کشف‌شده:**
- فایل شبح با کاراکتر newline (0x0A) در نام — غیرقابل حذف با git rm معمولی
- ۲۱ فایل `.bak` در backend و frontend
- Runtime data در گیت:
  - `backend/data/paper_trading/state.json`
  - `backend/data/paper_v2/state.json`
  - `backend/data/replay/state.json`
  - `backend/data/replay/trades.jsonl`
- `test_dispatcher_load.py` در روت پروژه
- backup فایل index گیت

**اقدامات:**
1. ✅ حذف فایل شبح با `git update-index --index-info` + `-z` separator
2. ✅ حذف همه .bak ها
3. ✅ انتقال runtime data از گیت به `.gitignore` (با حفظ روی دیسک)
4. ✅ پاکسازی فایل‌های روت
5. ✅ حذف index backup

**نتیجه:** گیت تمیز (از ۲۵۸ به ۲۵۱ فایل) ✅

---

### مرحله ۳: تمیزی کد (~۱ ساعت)

**مشکلات کشف‌شده:**

Backend (ruff):
- ۳ خطا: `Dict`، `Any` بی‌استفاده، متغیر `c` بی‌استفاده
- سینتکس: تمیز

Frontend (ESLint):
- `next lint` در Next.js 16 منسوخ شده
- ESLint نصب نبود
- ۱۲ warning در ۹ فایل (unused imports)

**اقدامات:**
1. ✅ رفع ۳ خطای backend با ruff
2. ✅ نصب ESLint 9 + config جدید (`eslint.config.mjs`)
3. ✅ رفع ۱۲ warning یکی‌یکی:
   - حذف `CardDescription`, `Play`, `Target`
   - حذف `formatNumber`, `CompareResultItem`
   - حذف `SignalType`, `useRouter`, `router`
   - حذف `cn`
   - رفع hook dependency در `signals-chart.tsx`

**نتیجه نهایی:**

| ابزار | قبل | بعد |
|-------|-----|-----|
| ruff | ۳ خطا | ✅ 0 |
| tsc | ✅ 0 | ✅ 0 |
| eslint | ۱۲ warning | ✅ 0 |

---

### مرحله ۴: ساختار پروژه (~۲ ساعت)

**زیرمرحله ۴.۱: سازماندهی scripts/ml (~۴۵ دقیقه)**

مشکل: ۵۸ فایل پایتون در یک پوشه، بدون تفکیک.

اقدامات:
- طراحی ساختار جدید با dry-run
- بررسی cross-imports (تأیید: هیچ‌کدام)
- انتقال ۵۶ فایل با `git mv` (تاریخچه گیت حفظ شد)

ساختار جدید:
```
backend/scripts/
├── tools/          (2 files - ابزار روزمره)
├── ml/             (3 files - ML فعال)
└── archive/
    ├── bottom_detection/   (6)
    ├── grid_bot/           (8)
    ├── volatility_hunter/  (3)
    ├── ml_experiments/     (21)
    ├── tests/              (12)
    └── debug/              (4)
```

**زیرمرحله ۴.۲: انتقال ML_JOURNEY.md**

- انتقال از `backend/` به `docs/` (با git mv)
- آپدیت `backend/README.md` برای ارجاع جدید

**زیرمرحله ۴.۳: کشف و رفع باگ بزرگ API Router (~۴۵ دقیقه)**

مشکل کلیدی: `31 failed, 45 passed`

ریشه:
- `main.py` فقط ۳ router رو include می‌کرد
- ۱۱ router دیگه اصلاً mount نشده بودند
- routerهای با prefix داخلی، مسیرهای double-prefix می‌ساختند

راه‌حل:
1. اضافه کردن `simulation` به master router
2. اضافه کردن prefix `/simulation` به simulation router
3. بازنویسی `main.py` برای استفاده از `v1_router` (master)

نتیجه شوکه‌آور:
- قبل: ۲۱ مسیر، ۳۱ تست فیل
- بعد: **۴۴ مسیر، ۷۶ تست پاس** ✅

---

### مرحله ۵: مستندات (~۲.۵ ساعت)

**۷ مستند جدید ساخته شد:**

| فایل | خطوط | توضیح |
|------|------|-------|
| docs/ARCHITECTURE.md | 665 | معماری کامل DDD + جریان داده |
| docs/SETUP.md | 475 | راه‌اندازی گام‌به‌گام |
| docs/API.md | 749 | ۴۴ endpoint در ۱۵ گروه |
| docs/BOTS.md | 563 | ۵ ربات + Adapter Pattern |
| README.md (روت) | 326 | بازنویسی کامل + badges |
| backend/README.md | 273 | بازنویسی از متن خام به markdown |
| docs/README.md | 237 | نقشه‌ی مستندات |

**+ گزارش‌های اضافی:**
- 2026-10-02_API_Router_Fix.md
- 2026-10-02_Scripts_Reorganization.md
- 2026-10-02_Project_Audit.md

**جمع کل:** ~۴۹۰۰ خط مستندات جدید 📚

**درس کلیدی:** ترمینال برای markdown پیچیده مناسب نیست — heredoc برای متن‌های طولانی با کاراکترهای خاص خراب می‌شود. راه‌حل: ادیتور گرافیکی (gedit) + copy از چت.

---

### مرحله ۶: تست‌ها (~۲۰ دقیقه)

**قبل:** ۳۱ failed, 45 passed
**بعد:** ۷۶ passed, 0 failed ✅

نکته: این مرحله جدا از مرحله ۴.۳ نیست — همون fix باعث شد همه تست‌ها پاس بشن. ولی جداگانه گزارش شده تا اهمیتش برجسته بشه.

---

## آمار نهایی

| متریک | قبل | بعد |
|-------|-----|-----|
| فایل‌های گیت | ۲۵۸ | ۲۵۱ |
| endpointهای API | ۲۱ | ۴۴ |
| تست‌های پاس | ۴۵ | ۷۶ |
| تست‌های فیل | ۳۱ | ۰ |
| ruff errors | ۳ | ۰ |
| eslint warnings | ۱۲ | ۰ |
| فایل‌های .bak | ۲۱ | ۰ |
| مستندات (خطوط) | ~۳۰۰ | ~۵۲۰۰ |
| API Keys لو رفته | ۱ | ۰ |

---

## کامیت‌های امروز (۲۲)

```
4f9e837 docs(readme): rewrite docs/README as navigation map
cf38fe5 docs(backend): rewrite backend README with markdown structure
195beaf docs(readme): rewrite README with badges, features, and doc links
4e89722 docs(bots): add comprehensive BOTS.md guide
dd86f3f docs(api): add comprehensive API.md reference
b7f1b53 docs(setup): add comprehensive SETUP.md guide
55fb29f docs(architecture): add comprehensive ARCHITECTURE.md
856f1d6 docs(reports): add API router fix report (2026-10-02)
98671f3 fix(api): mount all v1 routers via master router
c299b7c docs: move ML_JOURNEY.md to docs/
7b7d810 docs(reports): add scripts reorganization report (2026-10-02)
79e823a refactor(scripts): organize ML scripts into logical groups
ec3fddc docs(reports): add project audit report (security, git, code)
656df72 chore(lint): fix all ESLint warnings and unused variables
0bc56c4 chore(lint): setup ESLint 9 and cleanup backend imports
66117b3 chore: finalize gitignore updates and remove last .bak file
2abc71b chore: cleanup runtime data and backup files from git
0f53f6c chore(git): remove invalid index entry with newline path
1e3b18c chore: cleanup root directory
8c4e06d security: remove dox.xml from tracking, strengthen gitignore
8ec0666 chore(env): improve .env.example with security guidelines
0d66ee3 docs(reports): add simulator development report (2026-10-02)
```

---

## درس‌های آموخته

### ۱. امنیت اول از همه

هرگز API Key واقعی رو در فایل‌های یادداشت شخصی نذار. اگه لو رفت، **فوراً revoke کن**.

### ۲. regex برای کد خطرناکه

تلاش برای حذف خودکار importها با regex، فایل‌ها رو خراب کرد. راه درست: یکی‌یکی، با تأیید lint بعد از هر تغییر.

### ۳. ترمینال برای markdown مناسب نیست

heredoc و nano برای markdown با کاراکترهای خاص (backtick، asterisk، hash) مشکل دارن. راه‌حل: ادیتور گرافیکی.

### ۴. git نمی‌تونه با نام‌های عجیب راحت کار کنه

فایل با newline در نام، فقط با `git update-index --index-info` + `-z` حذف شد.

### ۵. تست‌ها می‌تونن باگ‌های پنهان رو کشف کنن

۳۱ تست فیل، ۱۱ router پنهان رو نشون داد که ۷ ماه بدون کسی متوجه نشده بود.

### ۶. git mv تاریخچه رو حفظ می‌کنه

۵۶ فایل با git mv منتقل شد، همه به‌عنوان rename تشخیص داده شدن (100% similarity).

### ۷. dry-run قبل از تغییرات بزرگ

قبل از انتقال ۵۹ فایل، dry-run زدیم که نشون داد چی به کجا میره. هیچ غافلگیری‌ای نبود.

---

## وضعیت نهایی پروژه

### امنیت
- ✅ API Keys در `.env` (gitignored، 600)
- ✅ هیچ کلید hardcoded در کد
- ✅ `.gitignore` قوی (pem, key, secrets, ...)

### گیت
- ✅ Working tree clean
- ✅ بدون فایل زائد
- ✅ `.gitignore` ۴۰+ خط

### کد
- ✅ ruff: 0 errors
- ✅ tsc: 0 errors
- ✅ eslint: 0 warnings

### تست
- ✅ 76/76 passed
- ✅ coverage در دسترس
- ✅ no integration gaps

### مستندات
- ✅ ۹ فایل اصلی
- ✅ ۷ گزارش روزانه
- ✅ ~۵۲۰۰ خط
- ✅ همه لینک‌ها معتبر

### معماری
- ✅ DDD + Hexagonal
- ✅ master router pattern
- ✅ Adapter Pattern برای ربات‌ها
- ✅ force-close در شبیه‌ساز

---

## قدم‌های بعدی

### کوتاه‌مدت

1. **CI/CD** — GitHub Actions برای اجرای خودکار تست‌ها و lint
2. **تست‌های integration** بیشتر برای endpointهای پوشش‌داده‌نشده
3. **گروه‌بندی services/** — ۲۷ فایل در روت، نیاز به ساختار

### میان‌مدت

4. **کش دیتابیس** برای کندل‌ها (SQLite/Postgres)
5. **WebSocket** برای قیمت لحظه‌ای
6. **Alembic** برای migrations (وقتی DB اضافه شد)

### بلندمدت

7. **Milestone 7: Order Execution** — اولین معامله‌ی واقعی
8. **Milestone 8: Live Trading** — بعد از تست کامل Paper Trading
9. **ML بازگشت** — بعد از ۶ ماه جمع‌آوری داده (طبق ML_JOURNEY)

---

## یادداشت پایانی

امروز، پروژه از یک وضعیت «قابل کار» به یک وضعیت «قابل اعتماد» تبدیل شد:

- **قبل:** بدهی فنی زیاد، مستندات ناقص، باگ‌های پنهان
- **بعد:** پایه‌ی محکم برای Milestone 7+

هیچ فیچر جدیدی اضافه نشد، ولی **کیفیت پروژه** چند برابر شد. این نوع کار «نامرئی» است ولی برای پایداری بلندمدت ضروری است.

---

**پایان گزارش — نسخه ۱.۰**
