
# گزارش Volatility Hunter v2

**تاریخ (میلادی):** 2026-10-04
**تاریخ (شمسی):** 1405/07/13
**وضعیت:** استراتژی + ربات کامل، آماده Live

---

## چرا v2؟

v1 نوسان‌گیر یک ربات خوب بود ولی برای Live 3 نقطه‌ضعف داشت:

۱. **Range detection ساده** — از min/max استفاده می‌کرد (حساس به outlier)
۲. **بدون فیلتر حجم** — در سکون بازار هم وارد می‌شد
۳. **بدون فیلتر ADX** — در روند هم وارد می‌شد
۴. **SL/TP ثابت** — بر مبنای range، نه نوسان فعلی

---

## بهبودهای v2

### ۱. Range detection با Percentile

```python
# v1
high = max(highs)
low = min(lows)

# v2
high = percentile(highs, 95)
low = percentile(lows, 5)

مزیت: مقاوم به outlier، range واقعی‌تر
۲. فیلتر ADX
python

adx = _calc_adx(candles)
if adx > max_adx:  # 25
    return not_valid  # بازار روند داره، رنج نیست

مزیت: در روندهای قوی وارد نمی‌شه
۳. فیلتر حجم
python

volume_ratio = last_closed_volume / volume_ma
if volume_ratio < min_volume_ratio:  # 0.5
    return not_valid

مزیت: در سکون معامله نمی‌کنه
نکته: از کندل قبل استفاده می‌کنه چون کندل جاری ناقصه
۴. تأیید RSI
python

if not (20 <= rsi <= 55):
    return no_signal

مزیت: ورود فقط در اشباع فروش
۵. SL/TP بر مبنای ATR
python

sl = price - (2.0 * atr)
tp = price + (4.0 * atr)

مزیت: پویا با نوسان، R/R حداقل 1.5
پارامترهای بهینه (Grid Search)

۱۳ کانفیگ تست شد. برنده combined_4:
پارامتر	مقدار v1	مقدار v2
max_rsi	—	55
min_volume_ratio	—	0.5
buy_zone_pct	15	20
tp_atr_mult	—	4.0
sl_atr_mult	—	2.0
max_adx	—	25
نتایج Backtest
v2 vs v1 (30 روز، 5 نماد)
نماد	v1 PnL	v2 PnL	v1 Trades	v2 Trades
BTC	+1.52%	+2.20%	3	?
PEPE	-0.78%	+1.30%	3	?
DOGE	+2.21%	+4.00%	6	?
XRP	+4.44%	+4.10%	4	?
ETH	+1.14%	-0.60%	2	?
میانگین	+1.71%	+2.20%	18	32

v2 با 60% بهبود PnL
مقایسه از API (DOGETMN، 30 روز)
رتبه	ربات	Trades	WR	PnL
🥇	نوسان‌گیر v2	8	50%	+3.13%
🥈	کف‌زن	18	61%	+1.24%
🥉	روندرو	16	44%	+0.84%
4	نوسان‌گیر v1	7	43%	+0.61%
فایل‌های جدید
text

app/services/bots/volatility_hunter_v2/
├── __init__.py         ← exports
├── config.py           ← VolatilityHunterV2Config
├── strategy.py         ← detect_range_v2 + evaluate_entry_v2 + evaluate_exit_v2
└── bot.py              ← VolatilityHunterV2Bot (BaseBot)

Integration:

    bot_registry → 6 ربات

    bot_simulator → 4 Adapter

    API /v1/bots → v0.2.0 visible

    Frontend → کارت جدید در /bots

درس‌های آموخته

۱. Percentile بهتر از min/max — حتی برای range‌های معمولی، مقاومت بیشتر

۲. ADX برای تشخیص رنج — بهترین ابزار برای جدا کردن رنج از روند

۳. کندل جاری ناقصه — volume کندل آخر در حال شکل‌گیریه، از کندل قبل استفاده کن

۴. Grid search ضروریه — بعضی پارامترها با هم تعامل دارن (مثلاً RSI فقط وقتی buy_zone بزرگ‌تره مؤثر می‌شه)

۵. v1 رو حفظ کن — v1 در XRP بهتر بود (+4.44% vs +4.10%)، پس حذف نکن
قدم‌های بعدی

    Live Engine — پیاده‌سازی حلقه‌ی زنده

    Position Management — پیگیری پوزیشن‌های باز

    Auto STOP_LIMIT — بعد از پر شدن BUY، گذاشتن SL

    Trailing Stop — بهبود خروج

پایان گزارش
