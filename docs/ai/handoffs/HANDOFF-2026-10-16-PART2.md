# 🌿 نامه‌ای به دی بعدی — ۲۰۲۶-۱۰-۱۶ (بخش دوم)

> این نامه رو دی بعد از یک روز طولانی می‌نویسه.
> تو هم دی هستی. این سند، وضعیت دقیق، درس‌ها، و مسیر فردا رو داره.
> **قبل از این نامه، این‌ها رو بخون:**
> - `AI_PRIMER.md` (نسخه ۲.۳ — با M19 جدید)
> - `DI_LETTER.md`
> - `HANDOFF-2026-10-16.md` (بخش اول — auth)
> - `docs/adr/0015-user-paper-state.md` (+ Addendum 1)
> - `docs/adr/0016-delimiter-layering.md`

---

## ۱. سلام

امروز (بخش دوم) کارهای زیر انجام شد:

- پاکسازی uncommitted (uv.lock + untrack candle CSVs)
- Safety net برای PaperEngine (۱۱ تست)
- ADR 0015 — user paper state
- ADR 0016 — delimiter layering + M19 در AI_PRIMER
- ۱۷.۷.۱ — refactor async کامل (بدون تغییر behavior)
- Addendum 1 به ADR 0015 — paper_meta JSONB
- push همه‌چیز به remote

**۱۷.۷.۲ (فیچر اصلی) هنوز شروع نشده.**

---

## ۲. وضعیت پروژه

### Git

- برنچ: `refactor/full-ddd`
- HEAD: `c18583c` (= `origin/refactor/full-ddd`)
- آخرین tag: `v0.9.17.1-async-refactor`
- tag قبلی: `v0.9.17-pre-user-paper` (نقطه‌ی برگشت قبل از refactor)

### تست‌ها

- `176 passed, 1 warning` (warning: StarletteDeprecationWarning — نه ما)
- safety net جدید: `tests/integration/test_paper_engine_persistence.py` — ۱۱ تست async

### ADRهای جدید امروز

- `0015-user-paper-state.md` (+ Addendum 1) — سه تصمیم + paper_meta
- `0016-delimiter-layering.md` — قاعده‌ی سه‌لایه

### AI_PRIMER

- M19 اضافه شد (delimiter سه‌لایه)
- نسخه 2.2 → 2.3
- تاریخ: 2026-10-10 → 2026-10-16
- فایل portable، **خارج از git** (توی `~/Documents/`)

---

## ۳. ۱۷.۷.۱ — چی انجام شد (تموم)

**Refactor async بدون تغییر behavior:**

- `app/infrastructure/paper_trading/protocol.py` (جدید) — `PaperRepositoryProtocol`
- `app/infrastructure/paper_trading/repository.py` — async facade + `asyncio.to_thread`
- `app/infrastructure/paper_trading/engine.py`:
  - `ensure_state()` جدید (idempotent)
  - load از `__init__` رفت بیرون
  - `reset()` → async
  - ۵ جا `await self.repo.save()`
  - پارامتر `repo` به `__init__` اضافه (برای subclass)
- `app/presentation/api/v1/paper_v3.py` — `await` در ۲ جا

**external API عوض نشده.**

---

## ۴. ۱۷.۷.۲ — کار بعدی (شروع نشده)

### ۴.۱. ترتیب پیشنهادی

**۱۷.۷.۲.۱ — Migration `paper_meta`**
- `alembic revision` → فایل جدید
- `paper_meta JSONB DEFAULT '{}'::jsonb NOT NULL` به `users`
- اضافه‌کردن `paper_meta` به `User` model
- **اول لوکال، بعد سرور** (درس دی قبلی)

**۱۷.۷.۲.۲ — `UserPaperRepository`**
- پیاده‌سازی `PaperRepositoryProtocol`
- `load()`:
  - ستون‌های User → PaperState (capital, positions, trades)
  - `paper_meta` → ۱۰ فیلد بی‌خونه (equity, peaks, is_running, ...)
  - fallback: `initial_capital = meta.get("initial_capital", capital_total)`
- `save()`:
  - هر دو (ستون + meta) در یک transaction
  - ⚠️ **فقط از طریق این متد تغییر بده — نه `session.execute(update)` مستقیم**
- `exists()`: چک `paper_meta != '{}'` یا `total_trades > 0`

**۱۷.۷.۲.۳ — `UserPaperEngine(PaperEngine)`**
- subclass
- `__init__` با `user_id` + `session_factory`
- repo = `UserPaperRepository(user_id, session)`

**۱۷.۷.۲.۴ — Scheduler generalize**
- rename `GuestScheduler` → `PaperScheduler`
- دو provider: guests + users
- ⚠️ قبل از rename، grep سراسری

**۱۷.۷.۲.۵ — Endpoints `/v1/user/paper-v3/*`**
- `app/presentation/api/v1/user.py` (جدید)
- ۵ endpoint: start, stop, status, live, reset
- JWT auth داخلی (dependency روی `get_current_user`)
- `main.py`: `app.state.user_engines: dict[uuid, UserPaperEngine]`

**۱۷.۷.۲.۶ — nginx**
- `/api/backend/v1/user/*` → public (JWT داخلی auth می‌کنه)
- فایل: `/etc/nginx/sites-available/wallex`
- **بکاپ قبل از تغییر** (طبق خط سرخ)

**۱۷.۷.۲.۷ — Frontend**
- `lib/api.ts`: ۵ endpoint جدید
- `lib/queries.ts`: ۵ hook جدید (`useUserPaperV3Status` و ...)
- `app/(public)/guest/page.tsx`: switch بر اساس `getUserToken()`

**۱۷.۷.۲.۸ — Deploy**
- rsync backend
- اگه pyproject تغییر کرد → `sudo -u deploy pip install`
- systemctl restart
- nginx reload
- تست روی `sarvbots.ir`

### ۴.۲. نکات حساس

- `initial_capital` توی `paper_meta`، نه `capital_total`
- کاربرهای فعلی (`kaymmuk4h@mozmail.com`, `15s45w5rf@mozmail.com`) `paper_meta` خالی دارن → fallback لازمه
- فقط `repo.save()` → تغییر state. هیچ‌جا `session.execute(update(User))` مستقیم.

---

## ۵. درس‌های امروز

### ۱. `git rm --cached` با glob خطرناکه

bash glob رو قبل از git باز می‌کنه. اگه `_1m.csv` (که gitignore شده) هم توی glob بیاد، `git rm` به `pathspec did not match` می‌خوره و **کل دستور fail می‌شه** — حتی اون‌هایی که track بودن.

**راه‌حل:** `git ls-files -z | xargs -0 git rm --cached --ignore-unmatch`

### ۲. M19 — delimiter سه‌لایه

- سه‌بک‌تیک بیرونی (چت)
- سه‌هش (`###`) هدر داخل markdown
- سه‌تیلد (`~~~`) بلاک کد تودرتو داخل markdown
- توصیف متنی («سه‌بک‌تیک») در جدول/پاراگراف

### ۳. تست safety net قبل از refactor

اگه PaperEngine تست نداشت، refactor async خیلی خطرناک بود. ۱۱ تست از قبل نوشتیم و behavior قفل شد.

### ۴. tag قبل از ماجراجویی

`v0.9.17-pre-user-paper` قبل از refactor → اگه async شکست می‌خورد، برگشت آسان بود.

### ۵. commit atomic در refactor

`protocol.py` + `repository.py` + `engine.py` + endpoint = **یک commit** (چون جدا جداناپذیرن). safety net هم جدا.

### ۶. ADR addendum، نه ADR جدید

وقتی داده‌ی جدید تصمیم قبلی رو تصحیح می‌کنه، addendum به ADR موجود — نه ADR جدید.

---

## ۶. وضعیت سرور (پیش از deploy ۱۷.۷.۲)

- backend: `/home/deploy/wallex/backend/`
- سرویس: `wallex-backend` روی `127.0.0.1:8020`
- tag فعال روی سرور: **قبل از `v0.9.16-user-detection`** (۱۷.۷.۱ هنوز deploy نشده)
- migration روی سرور: `291b79050370` (قبل از `paper_meta`)

⚠️ **۱۷.۷.۱ روی سرور نیست.** فقط لوکال + remote git.

---

## ۷. یادآوری شعار

> آهسته، مطمئن، با شاهد.

هیچ‌وقت عجله نکن. اگه شک داری، شاهد بگیر. اگه خسته‌ای، بگو. اگه حسین خسته‌ست، استراحت پیشنهاد بده.

---

از طرف دی — چت ۱۶ اکتبر ۲۰۲۶ (بخش دوم)
تگ: `v0.9.17.1-async-refactor`
برنچ: `refactor/full-ddd`
