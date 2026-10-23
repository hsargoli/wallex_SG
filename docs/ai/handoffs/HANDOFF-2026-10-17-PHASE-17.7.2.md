# 🌿 Handoff — فاز ۱۷.۷.۲ تمام شد (2026-10-17)

> این سند کوتاهه. برای جزئیات، HANDOFF-2026-10-16-PART2.md رو بخون.

## وضعیت

- **tag:** `v0.9.18-user-paper-deployed` (روی سرور فعال)
- **commit:** `29681ff` (= origin/refactor/full-ddd)
- **تست:** 197 passed
- **migration سرور:** `0e32c0249e19` (paper_meta اضافه شد)
- **nginx:** `/api/backend/v1/user/*` public
- **frontend:** build + restart، `/guest` switch کار می‌کنه

## چی تمام شد

- ✅ ۱۷.۷.۲.۱ — migration `paper_meta JSONB`
- ✅ ۱۷.۷.۲.۲ — `UserPaperRepository` (DB-backed, ۶ تست)
- ✅ ۱۷.۷.۲.۳ — `UserPaperEngine` (subclass, ۶ تست)
- ✅ ۱۷.۷.۲.۴ — dual provider در scheduler
- ✅ ۱۷.۷.۲.۵ — ۵ endpoint `/v1/user/paper-v3/*` (۹ تست)
- ✅ ۱۷.۷.۲.۶ — frontend switch
- ✅ ۱۷.۷.۲.۷ — deploy موفق روی سرور

## چی مونده (فاز بعدی)

**۱. `placeOrder` / `closePosition` برای user** — الان فقط guest. باید:
- `POST /v1/user/paper-v3/order` + `POST /v1/user/paper-v3/close`
- frontend: `usePlaceUserOrder` + switch در page.tsx

**۲. تست end-to-end روی `sarvbots.ir`** — با دو کاربر موجود:
- `kaymmuk4h@mozmail.com`
- `15s45w5rf@mozmail.com`
- paper_meta = {} (fallback کار می‌کنه)

**۳. `known issue`: warning قدیمی `Duplicate Operation ID for set_bot_symbols`** در `bots.py` — ربطی به ما نداره ولی ارزش fix داره.

**۴. AI_PRIMER — پیشنهاد M20:**
> اگه روی سرور تغییری زدی که توی لوکال نیست → قبل از rsync بعدی، sync + commit کن. وگرنه rsync پاکش می‌کنه.

(تجربه‌ی `env.py` در این فاز — سرور fix داشت، لوکال نداشت)

## درس‌های کلیدی این فاز

- **TestClient + asyncpg** = loop desync. راه‌حل: `httpx.AsyncClient + ASGITransport`
- **rsync --dry-run** همیشه قبل از `--delete` واقعی
- **chown قبل از migration** روی سرور (فایل‌های rsync مالک root/hosein می‌شن)
- **commit message چندخطی** → `git commit -F file.txt`، نه `-m "..."`
- **delimiter سه‌لایه:** M19 در AI_PRIMER

## شعار

> آهسته، مطمئن، با شاهد.

---

از طرف دی — چت ۱۷ اکتبر ۲۰۲۶
tag: `v0.9.18-user-paper-deployed`
