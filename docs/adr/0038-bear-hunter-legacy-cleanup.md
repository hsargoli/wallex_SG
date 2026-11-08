# ADR 0038 — bear_hunter Legacy Cleanup (Delete /bear-hunter + live_bot.py + specialized_backtest.py)

- **تاریخ:** 2026-11-08
- **وضعیت:** Proposed
- **نویسنده:** دی برگ (بر اساس نامه‌ی دی پرتو + شاهد امروز)
- **بازبین:** دی پرتو، دی نقشه‌دان
- **شاهدان:** نginx access log + DB check + git log (2026-11-08)

## Context

### وضعیت فعلی (شاهد)

پس از ADR-0037 (HumanSignal Nooaah)، investigation برای بدهی `live_bot.py` نشان داد **بدهی بزرگ‌تر از تصور اولیه** است:

1. **دو فایل** به `_archive.bear_hunter` وابسته‌اند:
   - `backend/app/presentation/api/v1/live_bot.py` (۶ endpoint)
   - `backend/app/presentation/api/v1/specialized_backtest.py` (backtest)

2. **Frontend فعالانه از `/bear-hunter` استفاده می‌کند**:
   - `frontend/app/(app)/bear-hunter/page.tsx` (۱ صفحه)
   - `frontend/components/bear-hunter/` (۴ کامپوننت)
   - `frontend/lib/api.ts` (۶ endpoint live-bot)
   - `frontend/lib/hooks/use-bear-hunter.ts` (۵ hook)

3. **تناقض با ADR-0034**: «Nooaah تنها ربات فعال» ولی `/bear-hunter` روی frontend فعال است.

### شاهد ترافیک (۲۰۲۶-۱۱-۰۸)

| شاهد | مقدار | تفسیر |
|---|---|---|
| `/bear-hunter` در ۲۴h | ۶ hit | همه از IP `2.144.3.130` (خودِ حسین) |
| `/v1/user/live-bot` calls | **۰** | هیچ‌کس از API استفاده نکرده |
| `users_with_trade_token` | **۰** (از ۹ کاربر) | هیچ‌کس نمی‌تواند short کند |
| آخرین کامیت bear-hunter | `d55d499` (۱۸ اکتبر) | > ۲۰ روز بدون کامیت |
| Sidebar link | `/bear-hunter` (خط ۴۶) | لینک هست ولی استفاده نمی‌شود |

**نتیجه:** صفحه `/bear-hunter` = **یتیم نمایشی** — نه API مصرف می‌شود، نه کسی می‌تواند trade کند.

### نظر معمار فنی (دی پرتو)

- **گزینه B (un-archive)**: ❌ منتفی — تناقض ADR-0034 + PF<1 در ۴ دوره
- **گزینه A (migrate به Nooaah)**: ۲-۳ روز (با ۴ قابلیت: bot_status, go_idle/resume, record_trade_open/add_realized_pnl, recompute_rolling_stats)
- **گزینه C (حذف کامل)**: ۲-۳ ساعت — با ۵ شرط

## Decision

**گزینه C — حذف کامل `/bear-hunter` + `live_bot.py` + `specialized_backtest.py`** (با شاهد ترافیک صفر).

### ۵ شرط (از دی پرتو)

1. **ترافیک nginx صفر** ✅ (شاهد: API=۰، users trade_token=۰)
2. **لینک از sidebar حذف شود** — `/bear-hunter` (خط ۴۶) → حذف
3. **کامپوننت‌های frontend پاک شوند** — `components/bear-hunter/` (۴ فایل) → حذف
4. **bear_hunter در _archive بماند** — `_archive/bear_hunter/` دست نمی‌خوره
5. **ADR-0034 اصلاح شود** — در همین ADR (بخش Consequences)

### لیست فایل‌های حذف‌شده

**Backend:**
- `backend/app/presentation/api/v1/live_bot.py` (159 خط)
- `backend/app/presentation/api/v1/specialized_backtest.py` (کامل)
- ثبت در `backend/app/presentation/api/v1/router.py` (خط ۷ و ۵۵) → حذف

**Frontend:**
- `frontend/app/(app)/bear-hunter/page.tsx`
- `frontend/components/bear-hunter/backtest-card.tsx`
- `frontend/components/bear-hunter/controls-card.tsx`
- `frontend/components/bear-hunter/signal-card.tsx`
- `frontend/components/bear-hunter/status-card.tsx`
- `frontend/lib/hooks/use-bear-hunter.ts`
- `frontend/lib/api.ts` — ۶ خط (`getBearHunter*`, `setSignal`, `killBot`, `resumeBot`)
- `frontend/components/layout/sidebar.tsx` — ۱ خط (`/bear-hunter` entry)

**Tests:**
- هیچ تستی برای bear_hunter در `tests/` نیست (فقط `_archive/bear_hunter/test_*.py` که دست نمی‌خوریم)

**پاک نمی‌شود:**
- `backend/app/services/bots/_archive/bear_hunter/` (طبق شرط ۴)
- `backend/app/services/bots/_archive/scalp_master/` (ربات دیگر آرشیو)
- ADR-0002 (sarv_tiger)، ADR-0019 (bear_hunter margin) — تاریخی، حفظ می‌شوند

### اصلاح ADR-0034

ADR-0034 در بخش Context نوشته بود:
> «Nooaah تنها ربات ML-based و سودده است.»

**اصلاح لازم:** به ADR-0038 اضافه شود که:
- bear_hunter از ۲۰۲۶-۱۰-۱۸ در آرشیو است
- صفحه `/bear-hunter` در ۲۰۲۶-۱۱-۰۸ حذف شد (ADR-0038)
- Nooaah تنها ربات فعال و قابل استفاده است

این اصلاح در قالب **ADR Addendum** (طبق درس ۲۷ V3 — Addendum برای تصحیح، نه ADR جدید) در انتهای ADR-0034 ثبت شود.

## Consequences

### مثبت
- ✅ حذف ۲ فایل backend (۳۰۰+ خط) + ۷ فایل frontend
- ✅ برطرف شدن تناقض با ADR-0034
- ✅ ساده‌سازی sidebar (لینک یتیم حذف)
- ✅ کاهش بار cognitive (کاربر فقط Nooaah می‌بیند)
- ✅ بدون ریسک کاربری (ترافیک صفر، users trade_token=۰)

### منفی
- ⚠️ از دست دادن `waiting_liquidity_since` + `current_regime` + `bot_status` (که Nooaah ندارد)
- ⚠️ اگر روزی short margin دوباره نیاز شد، باید معماری جدید (نه bear_hunter)
- ⚠️ کامیت `73d9c8a` (archive bear_hunter) حالا با حذف کامل جایگزین می‌شود

### خنثی
- 🟢 `_archive/bear_hunter/` حفظ می‌شود (برای تاریخچه، اگر نیاز شد)
- 🟢 ADR-0019 (bear_hunter margin) تاریخی می‌ماند

## Implementation Plan

### مرحله ۱ — حذف backend (۱۵ دقیقه)
1. `git rm backend/app/presentation/api/v1/live_bot.py`
2. `git rm backend/app/presentation/api/v1/specialized_backtest.py`
3. حذف import + include_router از `router.py` (خط ۷، ۵۵)
4. `python -m py_compile app/presentation/api/v1/router.py`
5. اجرای `pytest tests/` — هیچ تستی نباید بشکند (چون تستی برای live_bot نبود)

### مرحله ۲ — حذف frontend (۳۰ دقیقه)
1. `git rm "frontend/app/(app)/bear-hunter/page.tsx"`
2. `git rm frontend/components/bear-hunter/*.tsx`
3. `git rm frontend/lib/hooks/use-bear-hunter.ts`
4. حذف ۶ خط از `frontend/lib/api.ts` (grep `bear.hunter`)
5. حذف ۱ خط از `frontend/components/layout/sidebar.tsx`
6. `npx tsc --noEmit` — باید بدون خطا
7. `npm run build` — باید موفق

### مرحله ۳ — اصلاح ADR-0034 (۱۰ دقیقه)
1. اضافه کردن Addendum به انتهای ADR-0034

### مرحله ۴ — Deploy (طبق ADR-0037)
1. `npm run build` لوکال
2. `git bundle` + rsync + restart
3. Smoke test: `/bear-hunter` → **404** (انتظار)
4. Smoke test: `/dashboard`, `/nooaah`, `/research/tsfresh-backtest` → ۲۰۰

### مرحله ۵ — تست نهایی
- Regression: `pytest tests/` — همه‌ی ۳۲۹+۱۷ تست پاس
- Frontend: `npx tsc --noEmit` + `npm run build`
- Smoke: ۴ URL (dashboard, nooaah, tsfresh-backtest, research)

## Test Plan

| # | تست | انتظار |
|---|---|---|
| ۱ | `pytest tests/` | همه پاس (بدون تست bear_hunter) |
| ۲ | `npx tsc --noEmit` | بدون خطا |
| ۳ | `npm run build` | موفق |
| ۴ | `grep -r bear_hunter backend/app/` | فقط `_archive/` |
| ۵ | `grep -r bear-hunter frontend/` | فقط `_archive` (اگر هست) |
| ۶ | Smoke `/bear-hunter` | 404 |
| ۷ | Smoke `/dashboard`, `/nooaah` | 200 |

## منابع

- ADR-0034 (SarvBots = Analysis Platform) — تناقض، اصلاح می‌شود
- ADR-0037 (HumanSignal Nooaah)
- نامه‌ی دی برگ به دی پرتو (2026-11-08)
- پاسخ دی پرتو (2026-11-08) — تصمیم گزینه C
- شاهد ترافیک (2026-11-08): nginx access log + DB check + git log
- درس ۲۷ V3 (ADR Addendum برای تصحیح)
