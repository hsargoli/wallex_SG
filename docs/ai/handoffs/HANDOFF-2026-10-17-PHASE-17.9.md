# 🌿 Handoff — فاز ۱۷.۹ تمام شد (2026-10-17)

> نقطه‌ی امن: `v0.9.24.1-zebra-fix` + `v0.9.24-pnl-dashboard`

## وضعیت

- **tag:** `v0.9.24-pnl-dashboard` + `v0.9.24.1-zebra-fix`
- **تست backend:** 244 passed
- **روی سرور:** هم backend هم frontend
- **DB:** migration `0e32c0249e19` (paper_meta) — بدون تغییر

## ۱۷.۹ — چی تمام شد

### Backend
- ADR 0018 (FIFO vs Weighted — FIFO انتخاب شد)
- `app/services/wallex/cost_basis.py` — الگوریتم FIFO
- `app/services/wallex/service.py` — `compute_pnl()` (فقط cost basis)
- `GET /v1/user/wallex/pnl`
- ۲۰ تست جدید (۱۳ unit + ۷ integration)

### Frontend
- `useWallexPnl` hook
- PnL client-side محاسبه (backend فقط cost basis می‌ده، frontend قیمت فعلی از useMarkets)
- ستون‌های جدید: میانگین خرید، سود/زیان، تغییر از خرید
- tooltip روی همه‌ی ستون‌ها
- footer راهنما
- zebra striping

## کشف مهم

**View token به `GET /v1/account/orders` دسترسی داره!**
- ۲۵ سفارش برگشت برای `444xrlqlc@mozmail.com`
- فیلدها: `side`, `executed_qty`, `executed_price`, `executed_sum`, `fee`, `created_at`

## درس‌های امروز (برای AI_PRIMER v2.6 — پیشنهاد M26/M27)

### M26 — Deploy چک‌لیست (همیشه backend + frontend)
بعد از push، حتی اگه فقط یه سمت تغییر کرده، همیشه **هر دو** rsync + restart بشن — یا حداقل شاهد بگیریم که سمت دیگه روی سرور همون commit قبلیه. (تجربه‌ی `compute_pnl` که روی سرور نبود)

### M27 — `py_compile` ≠ runtime
`py_compile` فقط syntax رو چک می‌کنه، نه importهای runtime. `NameError: Decimal` فقط با pytest پیدا شد. **همیشه pytest هم بزن**، حتی برای تغییرات کوچیک.

### M28 — UI zebra/temp variables
برای رنگ‌های zebra در تم‌های روشن/تاریک، از `bg-black/[0.03] dark:bg-white/[0.05]` استفاده کن، نه `bg-muted` یا `bg-white/[X]` (که توی یه تم نامرئی می‌شن).

## کارهای باز (فاز ۱۷.۱۰ — طبق docs/ROADMAP-PNL-ENHANCEMENTS.md)

1. **تاریخچه معاملات (tooltip)** — نیاز: `GET /v1/user/wallex/orders?symbol=X` (اولویت ۱)
2. **Realized PnL** — مکمل مهم (اولویت ۲)
3. **Equity Curve** — نیاز به snapshot روزانه در DB
4. **مقایسه با BTC** — nice-to-have
5. **مالیات** — بعد از مشورت با حسابدار

## خط سرخ‌ها (بدون تغییر)

- `.env` سرور (`/home/deploy/wallex/.env`, chmod 600)
- کلید `WALLEX_TOKEN_ENC_KEY` (`/root/db_backups/20261017_pre_wallex/wallex_enc_key.bak`)
- پورت‌های Wallex: 8020 + 3020
- پروژه‌های دیگر روی سرور (noosharp, mabacheha, nourin)

## E2E تأیید شده

- `/dashboard`: PnL برای هر دارایی، مرتب بر اساس ارزش، zebra، sparkline
- `/settings/wallex`: اتصال، موجودی، قطع
- `/guest`: paper مستقل
- register → settings/wallex → dashboard

## شعار

> آهسته، مطمئن، با شاهد.

---

از طرف دی — چت ۱۷ اکتبر ۲۰۲۶
تگ: `v0.9.24.1-zebra-fix`
