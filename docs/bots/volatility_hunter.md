📊 نوسان‌گیر — Volatility Hunter Bot

slug: `volatility_hunter`
version: 0.1.0
وضعیت: ✅ آماده
تاریخ ایجاد: 2026-10-04
📖 استراتژی

Range Trading — خرید در کف محدوده، فروش در سقف.

فلسفه: وقتی بازار روند نداره و در یه محدوده نوسان می‌کنه، می‌تونیم از نوساناتش سود بگیریم. با تشخیص دقیق range و ورود در ۱۵٪ پایینی، ریسک رو کم و R/R رو بالا می‌بریم.
⚙️ پارامترها
پارامتر	مقدار	توضیح
`timeframe`	1h	تایم‌فریم
`lookback_candles`	48	دوره تشخیص range (۲ روز)
`min_range_pct`	3.0	حداقل range برای معامله
`max_range_pct`	12.0	حداکثر range (بالاتر = روند)
`min_atr_pct`	0.35	حداقل ATR%
`buy_zone_pct`	15.0	ناحیه خرید (نزدیک کف)
`sell_zone_pct`	15.0	ناحیه فروش (نزدیک سقف)
`stop_loss_pct`	2.0	SL
`take_profit_pct`	4.0	TP
`breakout_pct`	3.0	درصد شکست range
`position_size_pct`	30.0	۳۰٪ سرمایه
`max_positions`	3	حداکثر پوزیشن همزمان
`fee_pct`	0.2	کارمزد
`check_interval_sec`	300	فاصله بررسی
`warmup_candles`	100	کندل‌های اولیه

سرمایه اولیه: 300,000 USDT
🚦 منطق ورود
تشخیص Range معتبر

شرایط:

    ATR% ≥ 0.35 (نوسان کافی)

    Range% بین 3.0 و 12.0 (نه خیلی تنگ، نه روند)

    position_in_range ≤ 15٪ (نزدیک کف)

ورود

    اگه Range معتبر + قیمت در ناحیه خرید → ورود

    خروجی: `VolatilitySignal` با entry_price, stop_loss, take_profit

🛑 منطق خروج
دلیل	توضیح
`take_profit`	TP خورده (+4%)
`stop_loss`	SL خورده (-2%)
`breakout_up`	شکست سقف range (+3%)
`breakout_down`	شکست کف range (-3%)
`sell_zone`	قیمت به ناحیه فروش رسیده

خروج سریع: اگه range بشکنه، بلافاصله خارج می‌شیم.
⏱ تایم‌فریم

    1h (پیشنهادی و پشتیبانی‌شده توسط والکس)

    15m هم می‌شه ولی نیاز به بهینه‌سازی داره

📊 نتایج بک‌تست
بک‌تست ۳۰ روزه (ETHUSDT)
معیار	مقدار
بازدهی	+4.01%
تعداد معاملات	—
Win Rate	—

نکته: بهترین ربات عمومی از نظر بازدهی در تست ۳۰ روزه.
💪 نقاط قوت

    ✅ تشخیص دقیق range — با ATR% و range%

    ✅ ورود در کف — R/R بالا

    ✅ خروج سریع — در شکست range

    ✅ max_positions — مدیریت ریسک

    ✅ بهترین بازدهی در تست ۳۰ روزه

⚠️ نقاط ضعف

    ❌ در بازارهای رونددار ضعیف

    ❌ وابسته به تنظیمات ATR%

    ❌ نیاز به range معتبر (همیشه نیست)

⚙️ تنظیمات پیشنهادی
برای بازارهای رنج (ETH, ADA, DOGE)

    min_range_pct: 3.0

    max_range_pct: 12.0

    buy_zone_pct: 15.0

    stop_loss_pct: 2.0

    take_profit_pct: 4.0

برای بازارهای پرنوسان (SOL, AVAX)

    min_atr_pct: 0.5

    max_range_pct: 15.0

    stop_loss_pct: 2.5

🔗 لینک‌های مرتبط

    BOTS.md — فهرست کلی ربات‌ها

    README.md — ایندکس مستندات

    کد: `backend/app/services/bots/volatility_hunter/`

پایان مستند — نسخه 0.1.0
