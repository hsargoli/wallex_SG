# ADR 0032 — Server Drift Reconciliation (2026-11-01)

- **تاریخ:** 2026-11-01
- **وضعیت:** Accepted
- **نویسنده:** دی باران (با همکاری دی پرتو)
- **شاهدان:** دی دریا (CTO)، حسین (رهبر)

## زمینه (Context)

در 2026-11-01، drift بین سرور و لوکال شناسایی شد:
- سرور HEAD = `eb542496` (۲۳۶ commit عقب‌تر از لوکال)
- لوکال HEAD = `0bc6616`
- ۴۴ فایل uncommitted روی سرور
- `sarv_router/*.py` روی سرور حذف شده بود (فقط `__pycache__`)

## تصمیم (Decision)

**Fast-forward سرور به `0bc6616`، بدون تغییر runtime.**

1. Git bundle از لوکال (`wallex-local-0bc6616.bundle`) ساخته شد.
2. `git fetch` + `git merge --ff-only refs/remotes/local/fix` روی سرور.
3. Backup از uncommitted تغییرات (`/tmp/uncommitted-before-merge.patch`).
4. Runtime (.env, data/sarv_router/gate.json) حفظ شد.

## نتیجه (Result)

- سرور به `0bc6616` fast-forward شد.
- `sarv_router/*.py` بازگشت (bot.py, bot_lifecycle.py, store.py).
- Runtime حفظ شد (`.env`, `data/sarv_router/`).
- سایت `sarvbots.ir` سالم: `/` = 200 (85KB), `/health` = 200 (42B).
- ۳۸۶ تست unit روی سرور پاس شد.

## درس‌ها (Lessons)

### AP-64: Server Drift — تشخیص
- Drift را با `git rev-list --count origin/refactor/full-ddd..HEAD` و `git merge-base --is-ancestor` تشخیص بده.
- قبل از merge، `--ff-only` (نه merge معمولی) — برای fail-safe.

### AP-65: Uncommitted Changes — Backup قبل از merge
- `git diff > /tmp/uncommitted.patch` + `git status --short > /tmp/uncommitted-list.txt`.
- اگر merge تغییرات uncommitted را از بین برد، قابل بازیابی.

### AP-66: `ls -t | head -1` — ضد-الگو
- **هرگز** برای انتخاب فایل bundle از `ls -t | head -1` استفاده نکن.
- اسم bundle را صریح بگذار (`wallex-local-0bc6616.bundle`)، نه `bundle-latest`.

### AP-67: Domain Verify قبل از Smoke Test
- قبل از `curl` روی هر دامنه، `getent hosts <domain>` یا `dig +short <domain>` بزن.
- IP را با server IP (`185.143.234.133`) مقایسه کن.
- اگر متفاوت بود، **شاهد از منبع اشتباه است** — دامنه parking/alias شده.
- درس واقعی: `wallex.site` = GoDaddy parking (76.223.54.146)، نه سرور ما.

## Alternatives Considered

1. **`git reset --hard origin/...` (لوکال به سرور):** رد شد — ۲۳۶ commit از دست می‌رفت.
2. **`git merge` (بدون `--ff-only`):** رد شد — ممکن بود merge commit بسازد و history را شلوغ کند.
3. **`git pull`:** رد شد — سرور به github دسترسی ندارد.
4. **`--ff-only` + bundle:** ✅ پذیرفته شد (fail-safe، بدون merge commit).

## پیامدها

### مثبت
- سرور و لوکال همگام (`0bc6616`).
- `sarv_router` بازگشت (fix + 386 تست).
- Runtime حفظ شد.
- ADR + AP-64/65/66/67 ثبت شد.

### منفی
- orphan port 3000 (pid=1250579, root, v16.2.10) — cleanup بعدی.
- SSH key برای `deploy` ندارد (AP-26) — نیاز به investigation جداگانه.
- `alert_done` در `.bashrc` نصب نیست — نیاز به fix.

---

**تصویب:**
- دی باران (نویسنده) — 2026-11-01
- دی پرتو (بازبینی) — 2026-11-01
- دی دریا (CTO) — 2026-11-01
- حسین (رهبر) — 2026-11-01
