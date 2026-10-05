
# چارت حرفه‌ای + Fallback از تایم‌فریم بالاتر

**تاریخ (میلادی):** 2026-10-05
**تاریخ (شمسی):** 1405/07/15
**وضعیت:** کامل

---

## هدف

تکمیل چارت اختصاصی `/markets/[symbol]/chart` با:
- اطلاعات زنده (Info Cards + Crosshair Legend)
- اندیکاتورهای حرفه‌ای (RSI + MACD pane)
- سطوح Pivot/S/R
- شبیه‌سازی داده‌های قدیمی از تایم‌فریم بالاتر (چون والکس محدوده)

---

## کشف مهم درباره‌ی والکس

طبق مستندات رسمی والکس، تایم‌فریم‌های `15m`, `4h`, `8h`, `12h` پشتیبانی می‌شن. **ولی در عمل:**

| Resolution | معنی واقعی |
|-----------|------------|
| `"15"` | ۱ دقیقه (نه ۱۵ دقیقه!) |
| `"60"` | ۱ ساعت |
| `"D"` | ۱ روز |

**سقف داده‌ها:**
- `1m`: ~۲۵ روز
- `1h`: ~۲۹ روز (~۷۰۰ کندل)
- `1D`: ~۱ سال (~۳۷۰ کندل)

**نتیجه:** برای نمایش بازه‌های قدیمی‌تر با `1h`/`4h`، باید از `1D` شبیه‌سازی کنیم.

---

## کارهای انجام‌شده

### Backend

**کامپوننت‌های جدید:**
- `app/application/use_cases/candles_fallback_types.py` (26 خط)
  * `SyntheticRange` (from_ts, to_ts, source_tf)
  * `CandlesWithFallback` (candles, synthetic_ranges, counts)
- `app/application/use_cases/get_candles_with_fallback.py` (272 خط)
  * منطق fallback:
    - `15m`: فقط واقعی (از 1m aggregated)
    - `1h`: واقعی + شبیه‌سازی از `1D`
    - `4h`: واقعی (aggregated از 1h) + شبیه‌سازی از `1D`
    - `1D`: مستقیم
  * `_interpolate_day()`: تبدیل 1D به N کندل کوچک‌تر با درون‌یابی خطی
  * Dedup + sort برای جلوگیری از تداخل

**Endpoint جدید:**
- `GET /v1/markets/candles-v2/{symbol}?tf=1h&limit=500`
- Response:
```json
{
  "candles": [...],
  "synthetic_ranges": [
    { "from_ts": ..., "to_ts": ..., "source_tf": "1D" }
  ],
  "real_count": 695,
  "synthetic_count": 792
}

Frontend — کامپوننت‌های جدید

components/charts/chart-legend.tsx (157 خط)

    Crosshair Legend بالای چارت

    Row 1: زمان + OHLC + تغییر٪

    Row 2: EMA9, EMA21, BB

    Row 3: RSI, MACD, Signal, Hist

    Empty state: «موس رو روی چارت حرکت بده»

components/charts/chart-info-cards.tsx (266 خط)

    ۵ کارت اطلاعاتی: قیمت، حجم، نوسان، RSI، روند

    محاسبه‌ی روند از EMA9/21 + MACD (score -3..+3):

        +3 = صعودی قوی

        +2 = صعودی

        0 = بی‌طرف

        -2 = نزولی

        -3 = نزولی قوی

    تشخیص الگو از فاصله‌ی EMA:

        >0.5% = رونددار

        0.1-0.5% = در حال تغییر

        <0.1% = بازه‌ای

components/charts/pane-resize.tsx (48 خط)

    دکمه‌های [S] [M] [L]

    S=80px, M=120px, L=200px

    dir="ltr" برای RTL درست

Frontend — ارتقای ProChart

components/charts/pro-chart.tsx (235→~300 خط)

    Multi-pane chart با lightweight-charts v5

    Main pane: Candlestick + Volume

    Optional overlays: EMA 9/21, Bollinger

    RSI Pane (120px پیش‌فرض): RSI(14) + خطوط 70/30

    MACD Pane (120px پیش‌فرض): MACD + Signal + Histogram

    سطوح Pivot/S/R (از levels prop):

        Pivot: PP, R1, R2, S1, S2 (خطوط افقی)

        Swing: 6 سطح قوی/متوسط (dotted)

    Crosshair Legend callback: onCrosshairMove

    Synthetic candles: کندل‌های شبیه‌سازی با رنگ آبی rgba(96, 165, 250, 0.x)

    Zoom-out limit: onZoomOutLimit callback + clamp

    Resizable panes: rsiHeight/macdHeight props + setHeight بدون rebuild

Frontend — بازنویسی صفحه

app/markets/[symbol]/chart/page.tsx

    استفاده از useCandlesV2 (با fallback)

    Info Cards بالای چارت

    Layer toggles: EMA / BB / RSI / MACD / سطوح

    Pane Resize کنار toggles

    Crosshair Legend

    پیام zoom-out (کهربایی، ۳ ثانیه auto-dismiss)

    لینک به والکس اسپات + تذکر: «والکس ممکن است کندل‌های بیشتری داشته باشد»

    زوم اولیه: ۱۰۰ کندل آخر

Frontend — API Layer

    lib/api.ts: CandlesV2Response, SyntheticRange, getCandlesV2()

    lib/queries.ts: useCandlesV2() hook

نتایج
مورد	قبل	بعد
چارت	کندل + Volume	کندل + Volume + EMA + BB + Pivot/S/R
Panes	❌	RSI + MACD (قابل resize)
Crosshair	❌	Legend زنده
Info Cards	❌	۵ کارت با روند محاسبه‌شده
شبیه‌سازی fallback	❌	1h/4h از 1D
کندل‌های شبیه‌سازی	❌	آبی کم‌رنگ
محدودیت زوم	❌	پیام + clamp
لینک والکس	❌	✅ با تذکر
باگ‌های حل‌شده

۱. data must be asc ordered by time — کندل‌های synthetic و real هم‌زمان بودن → dedup + sort در backend
۲. چارت از بین می‌رفت هنگام resize pane — useEffect rebuild می‌کرد → paneRefs.setHeight() بدون rebuild
۳. RTL ترتیب دکمه‌های PaneResize — dir="ltr" روی container
۴. 1h کاملاً آبی می‌شد — cache issue مرورگر → hard refresh
درس‌های آموخته

۱. والکس فقط ۳ تایم‌فریم واقعی داره — بقیه سایلنت fallback می‌شن
۲. شبیه‌سازی از TF بالاتر راه‌حل بصری خوبیه (با شفافیت رنگ)
۳. pane.setHeight() برای تغییر ارتفاع بدون rebuild
۴. dir="ltr" برای RTL درست در کامپوننت‌های عددی
۵. حاشیه‌ی ۱۰٪ در محاسبه‌ی from_ts برای اطمینان
۶. createPriceLine برای سطوح افقی روی چارت
کامیت‌ها
text

8f4f275 feat(markets): backend fallback + markets page polish
6664ef2 feat(chart): resizable panes + synthetic candles + zoom limit
f8b0ae4 feat(markets): candles-v2 endpoint with fallback from higher TF
d553006 fix(scanner): click row → /markets/[symbol] (not chart)
8418170 Merge branch 'feature-day-2026-10-05'
18bcb4b feat(chart): crosshair legend + zoom controls

قدم‌های بعدی

    Drawing Tools (خط افقی، خط روند) — با localStorage

    Alerts (هشدار قیمت) — نیاز backend

    Replay Mode (بک‌تست بصری)

    Session Heatmap

    Multi-Chart Layout

پایان گزارش
