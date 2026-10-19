# 🩺 Incident Report: Server Git Drift & Missing Rate Limit

**تاریخ:** 2026-10-19
**نویسنده:** دی برکه
**وضعیت:** حل شد (Resolved)
**شدت:** متوسط (امنیتی — rate limit غیرفعال روی production)

---

## 🎯 خلاصه (TL;DR)

در حین بررسی برای merge به master و تگ v1.0.0، سه مشکل کشف و حل شد:

۱. **Drift سرور:** سرور (sarvbots.ir) روی commit `05dcfac` بود — جدا از لوکال (`57e9ec4`) و GitHub (`e6a38ae`).
۲. **rate limit غیرفعال:** `auth.py` روی سرور نسخه‌ی قدیمی (بدون `@limiter.limit(LOGIN_LIMIT)`) بود. Login روی production بدون محدودیت کار می‌کرد.
۳. **۷ فایل مستندات کهنه:** نسخه‌ی ۱۳ اکتبر در ریشه‌ی `docs/` سرور (untracked، بدون Deploy section، با «۱۰۰ تست» به‌جای ۳۲۹).

هر سه حل شد. لوکال، سرور و GitHub الان همه روی `c8e676a` و هم‌تراز.

---

## 🔍 کشف

در بلاک ۶ (بررسی منبع deploy)، `git branch -a` نشان داد `origin/master` وجود ندارد و سرور روی برنچ `refactor/full-ddd` است. اما `git log` سرور و لوکال فرق داشت:

| مکان | HEAD قبل از fix |
|------|-----------------|
| لوکال | `57e9ec4` (docs: env setup) |
| GitHub (`origin/refactor/full-ddd`) | `e6a38ae` (v0.9.29) |
| سرور | `05dcfac` (docs(nooaah)) |

`git merge-base --is-ancestor` تأیید کرد `05dcfac` نیای `57e9ec4` است — یعنی سرور عقب بود، نه واگرا. `git reflog` سرور نشان داد commitهای nooaah مستقیماً روی سرور زده شده‌اند (بدون push به GitHub).

---

## 🐛 ریشه‌یابی

**چرا سرور عقب بود؟**
- deploy با `rsync` انجام می‌شد (طبق `OPERATIONS.md`)، که فقط فایل‌ها را کپی می‌کند و HEAD سرور را جلو نمی‌برد.
- GitHub به‌روز نشده بود (push نشده بود)، پس سرور هم نمی‌توانست `git pull` کند.
- نتیجه: working tree سرور محتوای جدید داشت، ولی HEAD روی `05dcfac` قفل بود.

**چرا rate limit غیرفعال بود؟**
- `git checkout HEAD -- .` در بلاک ۱۹، `auth.py` را به نسخه‌ی `57e9ec4` برگرداند (با `@limiter.limit`).
- ولی پروسه‌ی uvicorn از ۱۱ ساعت پیش (۰۹:۲۰ UTC) اجرا می‌شد و کد قدیمی را در حافظه داشت.
- بدون restart، کد روی دیسک اعمال نمی‌شد.

**چرا ۷ فایل کهنه روی سرور بود؟**
- snapshot قدیمی ۱۳ اکتبر (قبل از restructure مستندات به زیرپوشه‌ها) که هرگز commit نشده بود.
- محتوا: بدون Deploy section، «۱۰۰ تست» (به‌جای ۳۲۹).

---

## 🛠️ راه‌حل

**۱. بکاپ (فاز ۰):**
- `wallex-server-backup-20261019-1842.tar.gz` (۱۳MB) — کل backend/ + frontend/
- `wallex-backup-code-20261019-1847.tar.gz` (۱.۵MB) — بدون node_modules/data/.git

**۲. هم‌ترازی HEAD سرور (بلاک ۱۸):**
- `git bundle` از لوکال به سرور منتقل شد (چون سرور به GitHub دسترسی ندارد — SSH port 22 timeout)
- `git fetch /tmp/wallex-57e9ec4.bundle refactor/full-ddd:refs/temp/incoming`
- `git reset --mixed 57e9ec4` — HEAD سرور به `57e9ec4` رفت، working tree دست نخورد
- نتیجه: status از ۱۲۴ به ۶۷ کاهش یافت

**۳. restore فایل‌های tracked (بلاک ۱۹):**
- `git checkout HEAD -- .` — همه‌ی ۴۵ فایل D و ۲۲ فایل M برگشتند
- `auth.py` با rate limit، `.gitignore` با entryهای جدید
- نتیجه: status به ۷ (فقط untracked docs) کاهش یافت

**۴. آرشیو مستندات کهنه (بلاک ۲۴A/۲۴B/۲۴C):**
- ۷ فایل از ریشه `docs/` سرور به `/tmp/server_old_docs_2026-10-19/` منتقل شد
- به لوکال منتقل و در `docs/archive/server_old_docs_2026-10-13/` آرشیو شد
- commit لوکال `c8e676a` + bundle + reset سرور
- نتیجه: status سرور = ۰، HEAD سرور = `c8e676a`

**۵. push به GitHub (بلاک ۲۵):**
- `git push origin refactor/full-ddd` → `e6a38ae..c8e676a`
- نتیجه: لوکال = سرور = GitHub

**۶. restart backend (بلاک ۲۶B):**
- `systemctl restart wallex-backend`
- verify: ۶ بار login → `401, 401, 401, 401, 401, 429` ✅
- production smoke test: همه‌ی مسیرها ۲۰۰ ✅

---

## 📚 درس‌ها

۱. **هیچ تغییری روی سرور بدون commit+push لوکال ممنوع.** (نقض M21)
۲. **`rsync` جای `git pull` را نمی‌گیرد.** rsync فقط فایل‌ها را کپی می‌کند؛ HEAD سرور را جلو نمی‌برد. باید یا `git pull` باشد یا بعد از rsync، `git reset --mixed` روی commit جدید.
۳. **بعد از هر تغییر `auth.py` یا `rate_limit.py`، حتماً restart + verify ۴۲۹.** بدون restart، کد جدید اعمال نمی‌شود.
۴. **قبل از هر deploy، `git status` سرور باید پاک باشد.** فایل untracked یا modified روی سرور یعنی drift.
۵. **`git bundle` راه‌حل قابل‌اعتماد برای سرورهای بدون دسترسی به GitHub است.** (SSH port 22 timeout → bundle + scp + fetch)
۶. **قبل از آرشیو/حذف فایل‌های قدیمی، mtime و محتوا را مقایسه کن.** mtime جدید لزوماً یعنی محتوای جدیدتر — بعد از `git checkout`، mtime عوض می‌شود ولی محتوا از HEAD می‌آید.

---

## ⏭️ کارهای باقی‌مونده

- **ADR دیپلوی:** قانون‌گذاری برای جلوگیری از تکرار این drift (اولویت بالا)
- **merge `master`:** ۲۲۶ commit عقب، بدون `origin/master` — fast-forward یا حذف
- **SMTP production:** بدهی فنی باقی‌مانده قبل از لانچ عمومی
- **تگ v1.0.0:** بعد از حل SMTP
- **حذف تکراری `README_OLD.md`:** در `docs/archive/server_old_docs_2026-10-13/` (identical با نسخه‌ی قبلی)

---

## 🧾 مراجع

- بلاک‌های ۶ تا ۲۶ (چت ۲۰۲۶-۱۰-۱۹)
- تگ `safety-before-merge-2026-10-19` روی `57e9ec4`
- تگ `server-pre-reset-2026-10-19` روی `05dcfac` (سرور)
- commit `c8e676a` (آرشیو مستندات)
- مشارکت: دی صحرا (تأیید reset --mixed)، دی فردوس (تأیید آرشیو)، حسین (اجرا)

---

**«آهسته، مطمئن، با شاهد، با بازبینی، با مهربانی.»**
