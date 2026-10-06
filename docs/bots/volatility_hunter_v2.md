📊 نوسان‌گیر v2 — Volatility Hunter v2 Bot

slug: `volatility_hunter_v2`
version: `0.2.0`
وضعیت: ✅ آماده (بدون Live Engine)
تاریخ ایجاد: 2026-10-05
📖 استراتژی

Range Trading پیشرفته — نسخه بهبودیافته v1 با فیلترهای بیشتر.

فلسفه: v1 ساده بود و فقط range رو می‌دید. v2 با ترکیب ADX (تأیید رنج)، RSI (اشباع فروش)، حجم (تأیید فعالیت)، و ATR (SL/TP پویا) سیگنال‌های دقیق‌تر و پایدارتر می‌ده.
⚙️ پارامترها
پارامتر	مقدار	توضیح
`timeframe`	1h	تایم‌فریم
`lookback_candles`	48	دوره تشخیص range
`range_low_pct`	5.0	صدک پایین (کف)
`range_high_pct`	95.0	صدک بالا (سقف)
`min_range_pct`	3.0	حداقل دامنه
`max_range_pct`	15.0	حداکثر دامنه
`min_atr_pct`	0.4	حداقل نوسان
`max_adx`	25.0	تأیید رنج (ADX پایین)
`min_volume_ratio`	0.5	حجم نسبت به میانگین
`buy_zone_pct`	20.0	ناحیه خرید
`min_rsi`	20.0	حداقل RSI
`max_rsi`	55.0	حداکثر RSI
`sl_atr_mult`	2.0	SL = entry - 2×ATR
`tp_atr_mult`	4.0	TP = entry + 4×ATR
`trail_atr_mult`	1.5	Trailing Stop
`max_duration_candles`	48	حداکثر ۴۸ ساعت
`breakout_pct`	3.0	خروج در شکست range
`position_size_pct`	30.0	۳۰٪ سرمایه
`max_positions`	2	حداکثر پوزیشن
`fee_pct`	0.2	کارمزد
`warmup_candles`	100	کندل‌های اولیه

سرمایه اولیه: 300,000 USDT
🚦 منطق ورود
فیلترهای تأیید

    ADX < 25 — تأیید رنج بودن (نه روند)

    Range% بین 3.0 و 15.0

    ATR% ≥ 0.4

    volume_ratio ≥ 0.5

    position_in_range ≤ 20٪

    RSI بین 20 و 55

ورود

اگه همه فیلترها پاس شدن → ورود با:

    entry_price = قیمت فعلی

    stop_loss = entry - 2×ATR

    take_profit = entry + 4×ATR

🛑 منطق خروج
دلیل	توضیح
`take_profit`	TP خورده (entry + 4×ATR)
`stop_loss`	SL خورده (entry - 2×ATR)
`trailing_sl`	Trailing Stop (پس از سود)
`breakout_up`	شکست سقف range
`breakout_down`	شکست کف range
`timeout`	۴۸ کندل گذشت
⏱ تایم‌فریم

    1h (پیشنهادی)

    15m نیاز به بهینه‌سازی داره

📊 نتایج بک‌تست
بک‌تست ۳۰ روزه (۵ نماد)
نسخه	معاملات	WR	PnL
قبل از بهینه‌سازی	23	34.8%	+1.37%
بعد از بهینه‌سازی	32	40.6%	+2.20%

بهبود: +0.83% PnL، +5.8% WR
💪 نقاط قوت

    ✅ Percentile-based range — مقاوم به outlier

    ✅ فیلتر ADX — فقط در رنج وارد می‌شه

    ✅ تأیید RSI — اشباع فروش

    ✅ فیلتر حجم — فقط در فعالیت

    ✅ SL/TP پویا — بر مبنای ATR

    ✅ Trailing Stop — محافظت از سود

    ✅ پایدارتر از v1

⚠️ نقاط ضعف

    ❌ Live Engine نداره (هنوز)

    ❌ بازدهی کمتر از v1 در ETH (+2.20% vs +4.01%)

    ❌ پارامترهای بیشتر = تنظیم سخت‌تر

    ❌ max_positions=2 (کمتر از v1)

⚙️ تنظیمات پیشنهادی
برای بازارهای رنج (ETH, ADA)

    max_adx: 25.0

    min_volume_ratio: 0.5

    max_rsi: 55.0

    buy_zone_pct: 20.0

برای بازارهای پرنوسان (SOL, AVAX)

    min_atr_pct: 0.5

    max_range_pct: 18.0

    sl_atr_mult: 2.5

🔗 لینک‌های مرتبط

    BOTS.md — فهرست کلی

    README.md — ایندکس

    volatility_hunter.md — نسخه v1

    کد: `backend/app/services/bots/volatility_hunter_v2/`

پایان مستند — نسخه 0.2.0
