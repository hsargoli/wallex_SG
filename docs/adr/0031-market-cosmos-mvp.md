# ADR 0031 — Market Cosmos (Isolated MVP)

- **تاریخ:** 2026-10-25
- **وضعیت:** Proposed → Accepted (CTO: دی دریا، رهبر: حسین)
- **نویسنده:** دی پرتو
- **شاهدان:** دی برکه (ناظر)، دی دریا (CTO)

---

## زمینه (Context)

حسین جان ایده‌ی «کیهان بازار» (Market Cosmos) را مطرح کرد: نمایش نمادها
به‌صورت ستاره‌های کهکشانی که **تدریجی** (progressive) ظاهر می‌شوند، برای
**چشم‌نوازی** (UX/visual appeal) و نه کاهش بار سرور.

**⚠️ نکته‌ی مهم (دی پرتو، ۲۰۲۶-۱۰-۲۵):**
انگیزه‌ی اصلی ایده (کاهش بار سرور) **قبل از شروع Cosmos حل شد** —
`/signals/batch` از ۳۰s به ۰.۵s رسید (commit `cb4c660`). پس Cosmos الان
**فقط ویژگی بصری/بازاریابی** است، نه ضرورت فنی.

## تصمیم (Decision)

**Isolated MVP** با ۶ گارد امنیتی:

1. **ترتیب:** tag `v1.1.0-launch` → ADR → کد (این سند).
2. **ایزولاسیون:** فقط ۲-۳ فایل جدید در `frontend/components/cosmos/`.
   صفر تغییر در بک‌اند، صفحات فعلی، `lib/queries.ts`، Navbar.
   صفر endpoint جدید در بک‌اند.
3. **Test-first:** `tsc --noEmit` = ۰ خطا + اسکرین‌شات دستی قبل از deploy.
4. **Time-box:** حداکثر **۳ ساعت**. اگر تمام نشد → توقف + گزارش.
5. **Deploy امن:** فقط `wallex-frontend` restart. Smoke test بعد:
   `sarvbots.ir` + `noosharp.ir` + `hosg.ir` (SERVER_INVENTORY).
6. **این ADR** قبل از شروع کد.

## پیاده‌سازی (Implementation Plan)

### فایل‌های جدید (فقط این‌ها)

frontend/app/(app)/cosmos/page.tsx ← route (Server Component)
frontend/components/cosmos/cosmos-canvas.tsx ← Canvas 2D renderer (Client)
text


### بدون تغییر
- ❌ `backend/` (صفر تغییر)
- ❌ `frontend/lib/queries.ts` (استفاده از hooks موجود)
- ❌ `frontend/app/(app)/signals/` + `scanner/` + `dashboard/`
- ❌ Navbar (Cosmos لینک در Navbar نمی‌گیرد — MVP فقط با URL مستقیم)
- ❌ `frontend/next.config.ts`

### داده (Data)
- استفاده از `useAllSignals(top50Symbols, "1h")` (موجود)
- `top50Symbols` از `useMarkets()` (موجود) — top 50 by volume
- **⚠️ هیچ fetch جدیدی در بک‌اند.**

### Progressive Reveal
- Client-side: `setInterval` هر ۱۰۰ms → ۱-۲ ستاره
- Total reveal: ~۵ ثانیه برای ۵۰ نماد (تجربه‌ی «تولد کهکشان»)
- **⚠️ اگر شاهد فاز ۰ نشان داد batch کند است** → fallback به batched fetch (بلاک جدا).

### طراحی بصری (پیش‌فرض MVP)
| مورد | مقدار |
|------|-------|
| ستاره | نقطه ۵-۸px + glow خفیف |
| رنگ | signal (buy=emerald, sell=red, hold=zinc, none=amber) |
| اندازه | بر اساس daily_volume (۵-۱۲px) |
| Layout | random scatter |
| Background | مشکی ساده |
| Animation | fade-in |
| Mobile | responsive (top 30 در موبایل) |
| Click | navigate به `/signals/{symbol}` |

## دلایل (Rationale)

- **چرا Isolated:** کاهش ریسک. اگر Cosmos شکست خورد، `git revert` فقط ۲ فایل
  را برمی‌گرداند — بدون آسیب به سایر صفحات.
- **چرا Canvas 2D (نه WebGL):** سبک‌تر (<۵KB بدون کتابخانه)، FPS کافی برای
  ۵۰-۲۹۷ ستاره، بدون ریسک crash روی موبایل قدیمی.
- **چرا client-side reveal (نه batch):** endpoint الان ۰.۵s است (cache-only).
  یک fetch + reveal تدریجی = UX خوب + کد ساده (۱ ساعت).

## پیامدها (Consequences)

### ✅ مثبت
- ویژگی بصری جذاب برای لانچ/بازاریابی
- ایزوله: revert آسان
- بدون بدهی فنی جدید در بک‌اند

### ⚠️ منفی
- Navbar link ندارد (کشف‌پذیری پایین در MVP)
- Mobile: top 30 فقط (نه ۲۹۷)
- Persian/English labels در Cosmos نیست (فاز polish)

## اقدامات پس از MVP

اگر بازخورد مثبت بود:
- **ADR 0032** (Cosmos Polish): کهکشان واقعی، halo، hover tooltip، Navbar link
- **ADR 0033** (cron DB): راه‌حل بلندمدت کندل‌ها

## ارجاعات

- `SERVER_INVENTORY_87.248.152.239.md` (خط سرخ‌ها)
- `AI_PRIMER.md` (شاهد، آهسته)
- `docs/NEXT_FEATURES.md` (ویژگی‌های فاز بعد)
- Commit `cb4c660` (perf signals — انگیزه‌ی اصلی Cosmos حل شد)

---

**تصویب:**
- دی پرتو (نویسنده) — 2026-10-25
- دی برکه (ناظر) — 2026-10-25
- دی دریا (CTO) — 2026-10-25
- حسین (رهبر محصول) — 2026-10-25
