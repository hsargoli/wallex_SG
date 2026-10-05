
# تفکیک تریدر تازه‌کار از حرفه‌ای

**تاریخ (میلادی):** 2026-10-05
**تاریخ (شمسی):** 1405/07/15
**وضعیت:** کامل

---

## هدف

صفحه‌ی `/signals/[symbol]` قبلاً **همه‌چیز** رو داشت:
- اطلاعات ساده (سیگنال، قیمت)
- اطلاعات حرفه‌ای (Rules Breakdown، Indicators Grid، Confluence، Multi-TF، Levels)

**مشکل:** تریدر تازه‌کار گیج می‌شد — «این RSI 79.5 یعنی چی؟»، «Volume Confirm BUY چیه؟»

**هدف:**
- `/signals/[symbol]` → تریدر تازه‌کار (ساده، آموزشی)
- `/markets/[symbol]` → تریدر حرفه‌ای (کامل، با tabs)

---

## کارهای انجام‌شده

### Backend
- (بدون تغییر)

### Frontend — کامپوننت‌های جدید

**components/signals/detail/** (برای هر دو صفحه):
- `simple-chart.tsx` (169 خط) — چارت ساده (فقط کندل + حجم)
- `signal-hero.tsx` (113) — هدر فشرده با signal + strength + tooltips
- `signal-cta.tsx` (93) — ۲ ردیف CTA، با prop `variant: beginner | advanced`
- `beginner-guide.tsx` (94) — ۳ کارت آموزشی (TP/SL، چرا این سیگنال، قبل از خرید)
- `_helpers.ts` — signalConfig + strengthLabel
- `confluence-card.tsx` (88) — تأیید متقابل TF
- `multi-tf-card.tsx` — کارت TF تکی
- `rule-row.tsx` — ردیف Rule

**components/markets/detail/** (برای tab تحلیل):
- `indicator-card.tsx` (100) — کارت اندیکاتور (نام + مقدار + وضعیت رنگی + progress + تفسیر)
- `indicators-grid.tsx` (199) — ۶ کارت: RSI، EMA21، MACD، Bollinger، ATR، Volume

**components/ui/**:
- `info-tip.tsx` (23) — tooltip با `title` attribute

### Frontend — بازنویسی صفحات

**app/signals/[symbol]/page.tsx:**
- ❌ حذف: Confluence، Multi-TF، Rules، Indicators، Levels، Trading Plan، Guide، SignalsChart
- ✅ افزودن: SignalHero، SimpleChart، SignalCta، BeginnerGuide
- ✅ simplification: MainSignal فقط Hero Card + SL/TP/RR
- ✅ tooltip روی سیگنال، قدرت، R/R، SL/TP، Confluence

**app/markets/[symbol]/page.tsx:**
- ✅ Tab navigation: `[تحلیل تکنیکال]` (پیش‌فرض) + `[معامله و دفتر سفارش]`
- **Tab تحلیل**:
  * SignalsChart (پیشرفته: EMA/BB/Levels)
  * SignalCta variant=advanced
  * ConfluenceCard
  * Multi-TF Grid (4 کارت)
  * IndicatorsGrid (6 کارت)
  * Rules Breakdown (با buy/sell score)
  * LevelsPanel
- **Tab معامله**:
  * MiniChart
  * OrderBookSummary
  * Order Book tables (Bids/Asks)
- TF picker مشترک بالای tabs

**app/markets/[symbol]/chart:**
- (دست‌نخورده)

---

## نتایج

| مورد | قبل | بعد |
|---|---|---|
| `/signals/[symbol]` خطوط | ۶۱۴ | ~۳۰۰ |
| `/markets/[symbol]` خطوط | ۲۸۳ | ~۴۰۰ |
| کامپوننت‌های مشترک | ۰ | ۱۰ |
| tooltip روی اصطلاحات | ❌ | ✅ |
| راهنمای آموزشی | ❌ | ✅ (۳ کارت) |
| تفکیک user journey | ❌ | ✅ |
| CTA هوشمند (beginner/advanced) | ❌ | ✅ |

---

## معماری نهایی

/signals/[symbol] ← تازه‌کار
├ SymbolSwitcher + TF
├ SignalHero (compact header)
├ SimpleChart (فقط کندل)
├ MainSignal (Hero Card + SL/TP/RR)
├ SignalCta variant=beginner
└ BeginnerGuide (۳ کارت آموزشی)

/markets/[symbol] ← حرفه‌ای
├ Header + MarketStats (ثابت)
├ Tab: تحلیل تکنیکال
│ ├ SignalsChart (EMA/BB/Levels)
│ ├ SignalCta variant=advanced
│ ├ ConfluenceCard
│ ├ Multi-TF Grid
│ ├ IndicatorsGrid (6 کارت)
│ ├ Rules Breakdown
│ └ LevelsPanel
└ Tab: معامله و دفتر سفارش
├ MiniChart
├ OrderBookSummary
└ Order Book Tables

/markets/[symbol]/chart ← چارت اختصاصی
text


---

## باگ‌های حل‌شده

۱. **ConfluenceCard/MultiTfCard** تعریف‌شده در `signals/[symbol]/page.tsx` بودن → استخراج به `signals/detail/`
۲. **CTA تکراری** در markets (می‌گفت «تریدر حرفه‌ای هستی؟» در حالی که خودش حرفه‌ایه) → `variant` prop
۳. **حذف ناقص AdvancedLink** با regex → patch دستی با python

---

## درس‌های آموخته

۱. **تفکیک user journey** از اول مهمه — نه بعداً
۲. **tooltip + آموزش** برای تازه‌کار حیاتیه
۳. **کامپوننت مشترک** بین دو صفحه = نگه‌داری راحت
۴. **regex برای حذف کامپوننت خطرناکه** — از python خطی استفاده کن
۵. **CTA شرطی با variant** — انعطاف‌پذیری بالا

---

## قدم‌های بعدی

- Tab «اطلاعات» در markets (حجم، ارزش معاملات، ...)
- Tooltip بیشتر در tab تحلیل markets
- Onboarding برای تازه‌کارها (tour)
- Help Center + واژه‌نامه

---

**پایان گزارش**
