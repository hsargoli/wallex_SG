# ⚡ اسکالپ‌مستر — Scalp Master Bot

**slug:** `scalp_master`
**version:** 0.1.0
**وضعیت:** ✅ آماده (Monitor Mode — فقط سیگنال)
**تاریخ ایجاد:** 2026-10-08

---

## 📖 استراتژی

اسکالپ نزولی: خرید پس از سقوط، فروش با سود کم.

**فلسفه:** بعد از سقوط شارپ، قیمت معمولاً یک بازگشت کوتاه دارد.
اگر RSI در محدوده‌ی اشباع فروش باشد و سقوط متوقف شود، ورود می‌کنیم.

---

## ⚙ پارامترها

| پارامتر | مقدار | توضیح |
|---------|-------|-------|
| `timeframe` | 1h | تایم‌فریم |
| `lookback_high` | 20 | تعداد کندل برای تشخیص سقف |
| `drop_threshold_pct` | 2.5 | حداقل افت از سقف (%) |
| `rsi_period` | 14 | دوره‌ی RSI |
| `rsi_min` | 25.0 | حد پایین RSI |
| `rsi_max` | 50.0 | حد بالای RSI |
| `min_body_ratio` | 0.3 | حداقل نسبت بدنه‌ی کندل |
| `sl_atr_mult` | 1.5 | ضریب ATR برای حد ضرر |
| `tp_atr_mult` | 3.0 | ضریب ATR برای حد سود |
| `min_sl_pct` | 1.5 | حداقل فاصله‌ی حد ضرر (%) |
| `max_dist_from_ema` | 5.0 | فیلتر سقوط آزاد |
| `timeout_candles` | 24 | حداکثر نگهداری (کندل) |
| `position_size_pct` | 30.0 | حجم پوزیشن (% سرمایه) |
| `fee_pct` | 0.2 | کارمزد |
| `warmup_candles` | 60 | کندل‌های اولیه |

---

## 🚦 منطق ورود

چهار شرط باید هم‌زمان برقرار باشند:

1. **تشخیص سقوط** — افت ≥ `drop_threshold_pct` از سقف `lookback_high` کندل اخیر
2. **توقف سقوط** — دو کندل سبز پشت سر هم
3. **RSI اشباع فروش** — `rsi_min ≤ RSI ≤ rsi_max`
4. **کیفیت کندل** — بدنه ≥ `min_body_ratio`

**حد سود/ضرر پویا:**
- SL = ورود − `sl_atr_mult` × ATR (حداقل `min_sl_pct`%)
- TP = ورود + `tp_atr_mult` × ATR

---

## 🔗 وابستگی‌ها

- `app.services.bots.base.BaseBot`
- `app.services.bots.scalp_master.config.ScalpMasterConfig`
- `app.services.bots.scalp_master.strategy.evaluate_entry`
- `app.services.indicators` (atr, ema, rsi)

---

## 📌 نکته

این ربات در حالت **Monitor** است — فقط سیگنال تولید می‌کند، سفارش نمی‌دهد.
