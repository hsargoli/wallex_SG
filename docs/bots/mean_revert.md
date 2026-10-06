🎯 کف‌زن — Mean Revert Bot

slug: `mean_revert`
version: `0.1.0`
وضعیت: ⚠️ آزمایشی (experimental)
تاریخ ایجاد: 2026-10-02
📖 استراتژی

خرید در کف، فروش در سود کوچک — با انتخاب استراتژی per-asset.

فلسفه: هر ارز رفتار خودش رو داره. بعضی رونددارن، بعضی نوسانی. به‌جای یه استراتژی ثابت، یه Smart Dispatcher داریم که برای هر ارز بهترین استراتژی رو انتخاب می‌کنه.
⚠️ هشدار مهم

این ربات برای تایم‌فریم 15m طراحی شده، ولی والکس این تایم‌فریم رو پشتیبانی نمی‌کنه.
مجبوریم روی 1h اجرا کنیم. نتایج ممکنه دقیق نباشن.

وضعیت در UI: با هشدار نمایش داده می‌شه.
⚙️ پارامترها
پارامتر	مقدار	توضیح
`timeframe`	15m	تایم‌فریم اصلی (اجباری: 1h)
`check_interval_sec`	180	فاصله بررسی
`max_positions`	3	حداکثر پوزیشن
`position_size_pct`	30.0	۳۰٪ سرمایه
`fee_pct`	0.2	کارمزد
`max_duration_candles`	20	timeout
`warmup_candles`	50	کندل‌های warmup
`min_avg_return`	0.3	آستانه انتخاب استراتژی
`min_stability`	0.5	آستانه پایداری

نکته: SL/TP تو `strategy_config.json` یا `paper_trader_v2` تنظیم می‌شن.
🚦 منطق
۱. Smart Dispatcher

    انتخاب استراتژی per-asset از `strategy_config.json`

    بر اساس: avg_return, stability, volatility

۲. استراتژی‌های موجود

    Simple Bot — کف‌شناسی قانونی برای ارزهای رونددار

    Bounce Scalper — برای ارزهای نوسانی (Fallback)

۳. تشخیص کف

    با score ≥ 6

    SL/TP تنظیم‌شده برای 1h

🛑 منطق خروج
دلیل	توضیح
`stop_loss`	SL خورده
`take_profit`	TP خورده
`timeout`	۲۰ کندل گذشت
⏱ تایم‌فریم

    15m (اصلی — ولی والکس نداره)

    1h (اجباری — با هشدار)

💪 نقاط قوت

    ✅ Per-asset strategy — هر ارز استراتژی خودش

    ✅ Smart Dispatcher — انتخاب خودکار

    ✅ Multi-timeframe — انعطاف‌پذیر

    ✅ Paper + Live + Backtest

⚠️ نقاط ضعف

    ❌ timeframe 15m پشتیبانی نمی‌شه — مجبور 1h

    ❌ experimental — نیاز به بهبود

    ❌ وابسته به `strategy_config.json`

    ❌ SL/TP تو config نیستن (پراکندگی)

⚙️ تنظیمات پیشنهادی
برای ارزهای رونددار (BTC, ETH)

    استراتژی: Simple Bot

    min_avg_return: 0.3

برای ارزهای نوسانی (SOL, DOGE)

    استراتژی: Bounce Scalper

    min_stability: 0.5

🔗 لینک‌های مرتبط

    BOTS.md — فهرست کلی

    README.md — ایندکس

    کد: `backend/app/services/bots/mean_revert/`

پایان مستند — نسخه 0.1.0
