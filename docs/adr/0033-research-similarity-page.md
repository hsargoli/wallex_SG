# ADR 0033 — Research Page: Historical Similarity Analysis (Insight Tool)

- **تاریخ:** 2026-11-03
- **وضعیت:** Accepted
- **نویسنده:** دی باران (با همکاری دی پرتو، دی دریا)
- **شاهدان:** حسین (رهبر)، دی پرتو (معمار فنی)

## زمینه (Context)

### چه شد که به این تصمیم رسیدیم؟

۱. **Research tsfresh (2026-11-02/03):** یک research دو روزه برای کشف edge جدید در BTCUSDT با tsfresh انجام شد. verdict: **no edge** (طبق AP-39، گزارش منفی = پیروزی).

۲. **ایده‌ی جدید حسین:** «اگر tsfresh edge برای معامله نمی‌دهد، آیا می‌تواند به‌عنوان **ابزار تحلیل** (Insight) به کاربر کمک کند؟ کاربر ببیند: الگوی فعلی BTC، شبیه کدام دوره‌های گذشته است، و بعد از آن دوره‌ها چه شد؟»

۳. **تفکیک insight از trading:**
   - Insight = اطلاعات برای تصمیم کاربر. ریسک مالی صفر.
   - Trading = سیگنال خودکار. ریسک مالی بالا، نیاز به edge واقعی (PF>1.2).
   - verdict «no edge» برای trading، insight را باطل نمی‌کند.

## تصمیم (Decision)

**صفحه‌ی جدید در `/research/tsfresh`** با این مشخصات:

### داده
- **۳ نماد:** BTCUSDT، ETHUSDT، SOLUSDT (از Binance zips).
- **بازه:** ۲۰۲۱-۰۱ تا ۲۰۲۶-۱۰ (۵+ سال).
- **منبع:** data.binance.vision monthly zips (نه API — بلاک شده).
- **ذخیره‌سازی:** Static JSON در `frontend/public/data/similarity-{SYMBOL}.json`.

### الگوریتم
- **پنجره:** ۲۴ ساعت (۲۴ کندل ۱h).
- **۱۹ feature:** RSI, ATR, MACD, EMA، حجم، نوسان، سایه‌ها، بدنه.
- **نرمال‌سازی:** Global Z-score (نه rolling).
- **متریک:** Cosine similarity.
- **K:** ۵۰ match (N>30 طبق AP-58).
- **افق:** ۲۴ ساعت forward return.

### UI
- Dropdown برای انتخاب نماد (BTC/ETH/SOL).
- ۳ بخش: الگوی فعلی، دوره‌های مشابه، بازده forward.
- رنگ‌بندی معنادار (bullish/bearish/extreme).
- جدول قابل سورت (تاریخ، شباهت، بازده).
- آمار بازه‌ای (۶ ماه اخیر، ۱ سال اخیر).
- Disclaimer: «نه سیگنال معاملاتی» + مقایسه با fee 0.65%.

### Refresh
- **MVP:** manual (اجرای `04_similarity.py`).
- **فاز ۲ (آینده):** cron job هر ۶ ساعت.

## پیامدها (Consequences)

### مثبت
- ✅ Insight برای کاربر، بدون ریسک مالی.
- ✅ Multi-symbol (BTC/ETH/SOL) — پوشش بهتر.
- ✅ ابزار تحلیل، نه سیگنال — از فریب کاربر جلوگیری می‌کند.
- ✅ Verdict tsfresh (no edge) به یک محصول تبدیل شد، نه شکست.

### منفی / ریسک
- 🟡 **Static JSON:** بدون refresh، داده کهنه می‌شود (badge «X روز پیش» در UI).
- 🟡 **Frontend complexity:** Dropdown + state management.
- 🟡 **Maintenance:** هر بار که data refresh می‌شود، ۳ JSON باید update شود.
- 🟡 **Binance API بلاک:** باید از zips استفاده کنیم (data.binance.vision) — کندتر.

### اقدامات آینده
1. **Refresh mechanism:** cron یا deploy hook (فاز ۲).
2. **Expand symbols:** BNB, XRP, ADA (اگر edge/insight ارزشمند بود).
3. **Similarity → SarvRouter:** بعد از Paper mode موفق، اگر similarity ارزش trading داشت (ADR جدید).

## منابع مرتبط
- `research/tsfresh/REPORT.md` — verdict no edge + این تصمیم
- `docs/NEXT_FEATURES.md` — ایده‌ی اولیه
- `docs/AI_PRIMER_V4.md` — AP-39, AP-57, AP-58, AP-62
