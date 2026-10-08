# گزارش توسعه — ۲۰۲۶-۱۰-۰۸
# Signals + Scanner + Market Detail

> یک روز کاری متمرکز روی صفحه‌های تحلیل و اسکنر
> نویسنده: حسین + دی (DeepSeek)
> محل: `~/wallex/backend` + `~/wallex/frontend`

---

## خلاصه‌ی یک‌خطی

صفحه‌ی Signals ساده و انسانی شد، صفحه‌ی Scanner کاملاً داده‌محور بازنویسی شد، و صفحه‌ی Market Detail یک چارت کوچیک + نگاه سریع تکنیکال گرفت.

---

## فاز ۰ — همگام‌سازی مستندات (بسته شد)

**مشکل:** اعداد مستندات با واقعیت فرق داشت (۷۶ تست/۴۷ endpoint/۱۵ صفحه در برابر ۱۰۰/۷۱/۱۹).

**کارهایی که انجام شد:**

- `docs/GETTING_STARTED.md` — ۱۱ جایگزینی (اعداد + مسیر `06-development`)
- `docs/README.md` — endpoint + طول فایل‌ها + typo `Shبیه‌ساز`
- `docs/CONVENTIONS.md` — ۱۰۰ تست + قاعده‌ی heredoc + افزودن مهر به تیم
- ساخت `docs/ROADMAP.md` (۶ فاز)
- ساخت `scripts/verify.sh` (بازتولیدپذیر)
- ساخت `docs/adr/` + ۵ ADR:
  - 0001-live-trading-default
  - 0002-branch-strategy
  - 0003-auth-deferred
  - 0004-heredoc-policy
  - 0005-bot-bak-cleanup

**معیار تمام شد:** `scripts/verify.sh` بدون اختلاف عددی.

---

## فاز ۳ — Candle Store (بسته شد)

**مشکل:** والکس فقط ۲۹ روز کندل می‌ده → backtest بلندمدت ممکن نیست.

**راه‌حل:** CSV store + cron روزانه.

- `backend/scripts/fetch_candles.py` — idempotent، atomic write
- `backend/data/candles/{BTCTMN,ETHTMN,USDTTMN}_1h.csv` — ۶۹۵ کندل هرکدام
- cron: `30 3 * * *` (روزانه ۳:۳۰ تهران)
- لاگ: `data/candles/fetch.log`

**معیار:** هر روز ۲۴ کندل جدید، بدون نیاز به دخالت دستی.

---

## ADR-0006 — منبع واحد Price Change

**باگ کشف‌شده:** `SANDTMN` در Signals عدد ۲.۸۶٪ نشان می‌داد، در Markets عدد ۳.۵۸٪، و در Wallex UI ۲.۹۴٪. سه عدد برای یک نماد.

**علت:** هر endpoint جداگانه محاسبه می‌کرد.

**راه‌حل:**
- `get_batch_signals` یک بار `exchange.get_markets()` می‌گیرد
- `market_map` به همه‌ی taskها پاس می‌شود
- `change_24h/7d` از Wallex (`24h_ch`, `7d_ch`)
- fallback: فقط اگر Wallex نداد، از کندل حساب می‌شود

**نتیجه:** همان عدد در Signals، Markets، و Wallex UI.

---

## صفحه‌ی Signals

**قبل:** جدول خشک از سیگنال‌ها بدون توضیح.

**بعد:**

- ۵ ستون تغییر: `1h | 24h | 7d | 1m | 1y`
- خط دلیل انسانی زیر نام نماد (`REASON_TRANSLATIONS`)
- رنگ rail بر اساس سیگنال (سبز/قرمز/خاکستری)
- گرید با عرض ثابت برای هدر و ردیف (بدون جابه‌جایی)
- میانگین بازه‌ی `1m` از کندل روزانه (نه ساعتی)

**نمونه:**

[↓] BTCTMN +0.93% [فروش]
چرا؟ نشانه‌ی شروع حرکت نزولی
text


---

## کارت «سیگنال دارایی‌های من» در Dashboard

**هدف:** کاربر ببیند دارایی‌های خودش چه وضعیتی دارند.

**پشت‌صحنه:**
- `GET /v1/account/cost-basis` — میانگین وزنی خرید هر نماد
- فیلتر: `BUY + FILLED + executed_qty > 0`
- برمی‌گرداند: `avg_buy_price`, `total_qty_bought`, `total_invested`, `buy_count`, `sell_count`

**فرانت:**
- حداکثر ۱۰ دارایی، بقیه در دکمه‌ی خط‌چین «N دارایی دیگر»
- P&L دقیق (بدون فشرده‌سازی K/M)
- tooltip: میانگین، قیمت فعلی، مقدار، سرمایه، P&L، تعداد خرید/فروش
- label: «در سود هستی» / «در ضرر هستی»

---

## صفحه‌ی Scanner — بازطراحی کامل

**فلسفه:** Scanner برای حرفه‌ای، Signals برای تازه‌کار. دو صفحه نباید یک چیز نشان بدهند.

**حذف شده:** بج سیگنال، قدرت، الگو، اسپارک‌لاین روند.

**اضافه شده (بک‌اند):**
- `ema_diff_pct` — اختلاف درصدی EMA(9) و EMA(21)
- `macd_hist` — هیستوگرام MACD
- `bb_pct` — موقعیت قیمت در باند بولینگر

**ستون‌های جدید:**

نماد | 24h | EMA 9/21 | MACD | RSI | R/R | ATR% | BB% | ۲۴ کندل
text


**KPI جدید:**
- اشباع فروش (RSI<30)
- MACD مثبت
- نزدیک کف باند (BB<20%)
- پرنوسان (ATR>2%)

**فیلترهای جدید:** EMA cross / MACD side / BB zone / RSI range / ATR min.

---

## صفحه‌ی Market Detail

**قبل:** چارت بزرگ ۴۲۰px + اندیکاتورها زیرش.

**بعد:**

- `ChartPreview` (کامپوننت reusable) — چارت کوچیک با دکمه‌ی «چارت کامل»
- `TechnicalSnapshot` — کارت ۵ سلولی: EMA / MACD / RSI / ATR / BB%
- چیدمان: چارت (1fr) + کارت‌ها (340px) کنار هم
- TF tabs از داخل کارت حذف شد (تکرار با بالای صفحه)

**SignalsChart:**
- prop جدید `bare` (بدون Card wrapper)
- prop جدید `visibleCandles` برای zoom

---

## درس‌های امروز

### ۱. کاراکترهای نامرئی در متن فارسی

`ZWNJ (U+200C)` و اعراب (`U+064B`) باعث می‌شوند `old` در Python پیدا نشود.

**راه‌حل:** به‌جای `replace(old, new)`، از index-based replacement استفاده کن یا اول `repr()` بگیر.

### ۲. مقایسه‌ی اعداد rolling

`24h_ch` هر لحظه عوض می‌شود. برای مقایسه‌ی دو منبع، باید **هم‌زمان** چک شوند.

### ۳. Tailwind JIT و grid پیچیده

`grid-cols-[minmax(0,1fr)_340px]` گاهی تولید نمی‌شود.

**راه‌حل:** `style={{ gridTemplateColumns: ... }}` قطعی‌تر است.

### ۴. کمپوننت تودرتو

`SignalsChart` خودش Card دارد. اگر در Card دیگری جا بگیرد → ارتفاع دوبار header+padding مصرف می‌شود.

**راه‌حل:** prop `bare`.

---

## خلاصه‌ی commits

| Commit | پیام |
|---|---|
| 358f86f | docs: add ADR + ROADMAP + verify.sh + 2 bot docs |
| 0455f0f | docs: sync with reality (100 tests, 71 endpoints, ...) |
| c2a1c52 | docs: fix last stale reference |
| 35a952f | feat(candles): add CSV candle store + fetch script |
| bc03457 | chore(gitignore): ignore candle fetch logs |
| 8bf4318 | fix(signals): unify change_24h/7d with Wallex |
| 56129a2 | feat(signals): add 1h/1m/1y columns + fixed grid + humanized reasons |
| 98f4de9 | feat(format): smart price formatter + faster market refresh |
| 8684100 | feat(scanner+market): technical-first design |

---

## بدهی فنی باقی‌مانده

- در Signals page، `1m` روی ۲۹ روز است. با cron روزانه رشد می‌کند.
- در `chart/page.tsx` (chart کامل) هنوز بازبینی نشده.
- `LIVE_TRADING_ENABLED=true` طبق ADR-0001 (تصمیم پذیرفته‌شده).
- ADR-0005 (پاک‌سازی .bak) — انجام شد در commit جدا.

---

**«آهسته، مطمئن، با شاهد، با بازبینی.»** 🌿
