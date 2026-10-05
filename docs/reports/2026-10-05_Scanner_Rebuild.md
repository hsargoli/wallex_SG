# بازسازی اسکنر بازار

**تاریخ (میلادی):** 2026-10-05
**تاریخ (شمسی):** 1405/07/15
**وضعیت:** کامل

---

## هدف

اسکنر بازار (`/scanner`) قبلاً یه فایل ۴۶۰ خطی بود که:
- خیلی از فیلترها کار نمی‌کردن
- KPI «صفحه» بی‌ربط بود
- سرچ فقط روی ۱۵ نماد صفحه‌ی جاری کار می‌کرد
- بدون timeframe selector
- بدون Sparkline، ATR%، tooltip
- ترتیب نمادها درست نبود

هدف: بازسازی کامل با معماری component-based، شبیه `/signals`.

---

## کارهای انجام‌شده

### Backend

- گسترش `_scan_one` در `app/presentation/api/v1/scanner.py`:
  - پارامتر جدید `tf` (پیش‌فرض `"1h"`)
  - محاسبه‌ی `rsi_14`, `atr_14`, `atr_pct`
  - import `atr, rsi` از `app.services.indicators`
- endpoint `/v1/scanner/scan`:
  - Query param جدید `tf`
  - echo `timeframe` در response

### Frontend — کامپوننت‌های جدید

components/scanner/
├── timeframe-tabs.tsx (15m/1h/4h/1D)
├── scanner-kpi.tsx (4 KPI cards with %)
├── scanner-filters.tsx (search, signal, strength, RSI, R/R)
├── scanner-table.tsx (با Popover tooltips)
├── scanner-table-row.tsx (9 ستون، click → chart)
└── sparkline.tsx (SVG 24-candle)
text


### Frontend — هوک‌های جدید

- `lib/hooks/use-scanner-url-state.ts`:
  - URL sync: `?tf=1h&signal=buy&rsiMin=30&...`
  - bookmarkable، back/forward کار می‌کنه
- `lib/hooks/use-paginated-scanner.ts`:
  - الگو کپی‌شده از `usePaginatedSignals`
  - chunk به chunk (10 تا)، تا به تعداد کافی match برسه
  - `totalScanned` / `totalSymbols` نمایش پیشرفت

### Frontend — بازنویسی

- `app/scanner/page.tsx`: **460 → 160 خط**
- `lib/api.ts`:
  - `scanSymbols(symbols, tf)`
  - `TrendResult` + 3 فیلد جدید
  - `ScannerScanResponse` + `timeframe`
- `lib/queries.ts`:
  - `useScanSymbols(symbols, tf)`

---

## ویژگی‌های اسکنر جدید

| # | ویژگی |
|---|-------|
| ۱ | TF tabs (15m/1h/4h/1D) با URL sync |
| ۲ | جستجوی سراسری روی همه‌ی ۱۸۷ نماد (نه فقط صفحه) |
| ۳ | Sort بر اساس `daily_quote_volume` (بیشترین حجم اول) |
| ۴ | حذف نمادهای بی‌حجم |
| ۵ | اسکن تدریجی با نمایش پیشرفت (N/187) |
| ۶ | صفحه‌بندی درست (مثل signals) |
| ۷ | KPI محاسبه روی نتایج فیلترشده |
| ۸ | Sparkline SVG (سبز/قرمز) |
| ۹ | ATR% با رنگ‌بندی (خاکستری/سبز/زرد) |
| ۱۰ | Popover tooltip روی هر هدر |
| ۱۱ | کلیک روی ردیف → `/markets/[symbol]/chart` |
| ۱۲ | حذف KPI «صفحه» (بی‌ربط) |

---

## نتایج

| مورد | قبل | بعد |
|---|---|---|
| خطوط `page.tsx` | ۴۶۰ | ۱۶۰ |
| فیلترها | صفحه‌محور | سراسری |
| Timeframe | ❌ | ✅ 4 TF |
| Sort | ثابت | حجم نزولی |
| Tooltip | ❌ | ✅ Popover |
| Sparkline | ❌ | ✅ SVG |
| ATR% | ❌ | ✅ رنگ‌بندی |
| صفحه‌بندی | شبه‌کار | کپی signals ✅ |

---

## باگ‌های حل‌شده

1. **KPI «صفحه»** — کارت بی‌ربط حذف شد
2. **هدر شکسته** — «107 مارکت 13» → «صفحه ۱ از ۱۳ — N/187»
3. **سرچ صفحه‌محور** — الان کل ۱۸۷ نماد
4. **R/R خالی** — از backend میاد، بعضی نمادها ندارن (طبیعیه)
5. **صفحه‌بندی غلط** — با الگوی signals fix شد

---

## درس‌های آموخته

۱. **الگوی signals الگوی خوبیه** — برای هر صفحه‌ی لیست‌محور دیگه هم قابل استفاده‌ست:
   - `useMarkets` برای لیست سبک
   - `usePaginated*` برای lazy fetch + filter + pagination

۲. **هیردوک تکه‌تکه** — فایل‌های بزرگ‌تر از ۱۰۰ خط باید chunk بشن، وگرنه paste خراب می‌کنه.

۳. **python patch به جای sed** — برای ویرایش‌های چند-خطی، python امن‌تره.

۴. **اول کد فعلی رو ببین** — Popover از قبل بود، اشتباهاً دنبال ساخت SimpleTooltip رفتیم.

۵. **checkpoint tag** — قبل از هر refactor بزرگ، tag بزن (این بار `checkpoint-before-scanner-rebuild`).

---

## کامیت‌ها

4da07a9 feat(scanner): add tf param + RSI/ATR indicators to /scan
(بعدی) feat(scanner): rebuild with URL state, lazy scan, volume sort
text


---

## قدم‌های بعدی

- server-side filter endpoint (برای سرعت بیشتر روی ۱۸۷+ نماد)
- چارت حرفه‌ای `/markets/[symbol]/chart` با EMA/RSI/MACD
- تست unit برای توابع اندیکاتورها
- WebSocket برای قیمت زنده

---

**پایان گزارش**
