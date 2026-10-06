🧠 پورتفوی هوشمند — Smart Portfolio Bot

slug: `smart_portfolio`
version: `0.1.0`
وضعیت: ⚠️ آزمایشی (multi-asset)
تاریخ ایجاد: 2026-10-03
📖 استراتژی

تخصیص سرمایه بین چند ربات بر اساس رژیم بازار — یه meta-bot.

فلسفه: هیچ رباتی تو همه شرایط خوب نیست. trend_follow تو روند، mean_revert تو رنج، grid_bot تو رنج پایدار. به‌جای انتخاب دستی، یه مدیر داریم که:

    رژیم فعلی رو تشخیص می‌ده

    ربات‌های مناسب رو انتخاب می‌کنه

    سرمایه رو بین‌شون تقسیم می‌کنه

نکته: این ربات خودش تصمیم ورود/خروج نمی‌گیره — فقط تخصیص می‌ده.
⚙️ پارامترها
پارامتر	مقدار	توضیح
`total_capital`	300,000	کل سرمایه
`timeframe`	1h	تایم‌فریم
`max_concurrent_bots`	2	حداکثر ربات همزمان
`rebalance_interval_min`	60	فاصله rebalance
نقشه رژیم → ربات
رژیم	ربات‌ها	وزن
`trending_up`	trend_follow	1.0
`ranging`	mean_revert + grid_bot	0.6 + 0.4
`choppy`	volatility_hunter	1.0
`trending_down`	—	هیچ
نامشخص	mean_revert + volatility_hunter	0.5 + 0.5
🚦 منطق
۱. تشخیص رژیم

    با `regime_detector.py`

    رژیم‌ها: trending_up, trending_down, ranging, choppy

    خروجی: RegimeResult با regime, confidence, reasons

۲. تخصیص

    بر اساس regime_map

    هر ربات یه BotSlot می‌گیره با weight و capital_allocated

    is_safe اگه رژیم مناسب نباشه false می‌شه

۳. اجرا

    هر ربات جداگانه تصمیم می‌گیره

    Rebalance هر ۶۰ دقیقه

🛑 منطق خروج
دلیل	توضیح
`trending_down`	روند نزولی → همه غیرفعال
`rebalance`	رژیم عوض شد
`is_safe=false`	رژیم نامناسب
⏱ تایم‌فریم

    1h (پیشنهادی)

💪 نقاط قوت

    ✅ Meta-bot — مدیریت ربات‌های دیگر

    ✅ Regime-based — هر رژیم، ربات مناسب

    ✅ Multi-strategy — ترکیب ۴ ربات

    ✅ Rebalance — تطبیق با تغییر رژیم

    ✅ Safe mode — در روند نزولی غیرفعال

⚠️ نقاط ضعف

    ❌ multi-asset — برای شبیه‌سازی تک‌نماد مناسب نیست

    ❌ وابسته به `regime_detector` دقیق

    ❌ max_concurrent_bots=2 (محدود)

    ❌ هنوز تو production تست نشده

⚙️ تنظیمات پیشنهادی
برای بازارهای رونددار (BTC, ETH)

    regime_map.trending_up: trend_follow وزن 1.0

    max_concurrent_bots: 1

برای بازارهای رنج (ADA, DOGE)

    regime_map.ranging: mean_revert + grid_bot

    max_concurrent_bots: 2

    rebalance_interval_min: 30

برای بازارهای choppy (SOL, AVAX)

    regime_map.choppy: volatility_hunter وزن 1.0

🔗 لینک‌های مرتبط

    BOTS.md — فهرست کلی

    README.md — ایندکس

    regime_detector.py — تشخیص رژیم

    کد: `backend/app/services/bots/smart_portfolio/`

پایان مستند — نسخه 0.1.0
