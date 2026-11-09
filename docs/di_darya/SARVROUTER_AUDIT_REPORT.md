# 🔍 SarvRouter Audit — آمادگی Live

> **نسخه:** 1.0
> **تاریخ:** ۲۰۲۶-۱۱-۰۹
> **نویسنده:** دی دریا (CTO) — به درخواست دی کویر
> **مبنا:** پرایمر v3.1 (قانون ۱۸: ۵ لایه)، R25-R27
> **شاهد:** خروجی ترمینال ۲۰۲۶-۱۱-۰۹، فایل‌های bot.py (125 خط)، bot_lifecycle.py (137 خط)، test_sarv_router_lifecycle.py (117 خط)، SARVBOTS_STATE_2026-11-09.md، ADR-0037/0038
> **وضعیت شاهد:** کامل برای ۴ فایل بالا. **ناقص** برای tests دیگر (۱۱ فایل ادعا شده) — بخش ۴.

---

## ۰. خلاصه مدیریتی

SarvRouter از نظر منطق چرخش، بالغ است: lifecycle با stability_window، cooldown، fail-safe روی start error، و بازیابی state بعد از restart (hydrate_from_state). اینها با شاهد تأیید شد.

**اما برای Live، سه شکاف بحرانی هست:**
1. لایه‌های ۱ (`is_trading_enabled`) و ۲ (`live_stage`) در بدنه‌ی `bot.py` هیچ ارجاعی ندارند — صفر grep. طبق قانون ۱۸، اینها باید **در ربات** چک شوند، نه فقط در API.
2. SIGTERM / signal handling صفر است. R25 باز است.
3. `expires_at` صفر است. R26 باز است.

**نتیجه:** `ready_for_live = False`. برای Paper mode مشکلی نیست، ولی برای Live نیاز به سه اقدام قبل از تأیید است (بخش ۷).

---

## ۱. پاسخ به چهار سؤال دی کویر

### ۱.۱. `live_stage` جلوی ترید در مرحله ۰/۱ را می‌گیرد؟

**پاسخ: خیر.**
- **شاهد:** grep روی `sarv_router/` برای `live_stage|is_trading_enabled` → **صفر نتیجه**.
- **تحلیل:** طبق `SARVBOTS_STATE_2026-11-09.md` بند ۳، این لایه‌ها در `user.py` و `user_bot_config.py` هستند (سطح API). این برای همان لحظه‌ی فراخوانی کافی است، اما **اصل defense-in-depth** می‌گوید ربات هم باید مستقلاً چک کند. اگر باگ API یا مسیر فراخوانی دیگری (scheduler، backtest_adapter) وارد شود، ربات بدون فیلتر شروع می‌کند.
- **ریسک:** اگر `scheduler.py` مستقل از وضعیت کاربر `tick()` را صدا بزند، لایه‌ی ۱ و ۲ کاملاً دور زده می‌شوند.
- **اقدام لازم:** افزودن دو چک در `bot.py` بلافاصله بعد از `store.load()` — قبل از kill_switch.

### ۱.۲. مکانیزم بستن ایمن (SIGTERM) پیاده شده؟

**پاسخ: خیر.**
- **شاهد:** grep روی `SIGTERM|signal|timeout|expires_at` روی `sarv_router/` → **خروجی خالی**.
- **تحلیل:** در `systemd restart`، در `docker stop`، در قطع ناگهانی — بدون signal handler، پوزیشن‌های باز رها می‌شوند و `stop_all()` اجرا نمی‌شود.
- **اقدام لازم:** افزودن `signal.signal(SIGTERM, handler)` که `_safe_stop_all()` + `audit.log` را صدا بزند. سپس `os._exit(0)` در صورت اتمام موفق.

### ۱.۳. `daily_loss_limit_pct` و `kill_switch` درست چک می‌شوند؟

**پاسخ: ناقص.**

**kill_switch — ✅ درست:**
- **شاهد:** `bot.py:56` (`if state.kill_switch_manual or state.kill_switch_auto`)، `store.py:23-24` (تعریف هر دو فیلد).
- **تحلیل:** هر tick از `store.load()` می‌خواند، پس تغییر manual در DB بلافاصله اثر می‌کند.

**daily_loss_limit — ⚠️ منطق هست، واحد نامعلوم:**
- **شاهد:** `bot.py:65` (`if state.daily_pnl_pct <= -self.config.daily_loss_limit_pct`)، `config.py:32` (`daily_loss_limit_pct: float = 2.0`).
- **تحلیل:** اگر `daily_pnl_pct` درصدی باشد (مثلاً `-2.0` یعنی -۲٪)، درست کار می‌کند. اگر کسری باشد (`-0.02`)، آستانه هرگز فعال نمی‌شود چون `-0.02 > -2.0`.
- **شاهد غایب:** هیچ‌جا در `sarv_router/` نمی‌بینم که `daily_pnl_pct` **مقداردهی** شود. باید در ماژول PnL خارج از این پوشه باشد.
- **اقدام لازم:** grep سراسری روی `daily_pnl_pct` و `daily_loss_limit_pct` برای تأیید واحد.

**audit gap — ❌ در manual kill:**
- **شاهد:** `bot.py:56-62` (مسیر kill_switch manual) → `audit.log` **صدا زده نمی‌شود**. مقایسه با `bot.py:71-79` (مسیر daily_loss) که هم `kill_switch_auto=True` می‌کند هم audit می‌نویسد.
- **تحلیل:** نقض لایه‌ی ۵ (audit per-user) برای حالت manual. اگر کاربری kill_switch بزند، اثری در `audit.jsonl` نمی‌ماند.

**`_safe_stop_all` بی‌صدا:**
- **شاهد:** `bot.py:33-37` — `except Exception: pass`.
- **تحلیل:** اگر `stop_all()` به هر دلیلی fail شود (مثلاً API والکس down)، هیچ اثری نمی‌ماند. این ضعف در حالت Live بحرانی است: کاربر فکر می‌کند ربات متوقف شده، ولی نیست.

### ۱.۴. بدهی `expires_at` هنوز وجود دارد؟

**پاسخ: بله، باز است.**
- **شاهد:** grep روی `sarv_router/` → **خروجی خالی**. هم در bot.py و bot_lifecycle.py و هم در test، هیچ ارجاعی به `expires_at` نیست.
- **تحلیل:** R26 همچنان باز است. این بدهی از handoff دی پرتو به دی کویر منتقل شده (طبق SARVBOTS_STATE بند ۴).
- **اقدام لازم:** تعریف معنای دقیق `expires_at` (چه چیزی منقضی می‌شود؟ gate؟ HumanSignal؟ سفارش؟) — قبل از پیاده‌سازی.

---

## ۲. جدول انطباق ۵ لایه قانون ۱۸ (در SarvRouter)

| لایه | نام | وضعیت | شاهد |
|---|---|---|---|
| ۱ | `is_trading_enabled` | ❌ در bot غایب | ۰ ارجاع |
| ۲ | `live_stage` | ❌ در bot غایب | ۰ ارجاع |
| ۳ | `daily_loss_limit` | ⚠️ منطق هست، واحد نامعلوم | `bot.py:65`, `config.py:32` |
| ۴ | `kill_switch` (manual + auto) | ⚠️ auto ✅، manual بدون audit ❌ | `bot.py:56`, `store.py:23-24` |
| ۵ | `audit per-user` | ⚠️ switch ✅، daily_loss ✅، manual kill ❌ | `audit.py:35`, `bot.py:71` |

**نتیجه:** طبق قانون ۱۸ («بدون این ۵ لایه، هیچ رباتی نباید در حالت Live کار کند»)، SarvRouter **مجوز Live ندارد**.

---

## ۳. یافته‌های تکمیلی (فراتر از ۴ سؤال)

| # | یافته | شدت | شاهد |
|---|---|---|---|
| F1 | `_safe_stop_all` استثناها را می‌بلعد (بدون لاگ) | 🔴 | `bot.py:33-37` |
| F2 | manual kill_switch در audit ثبت نمی‌شود | 🟠 | `bot.py:56-62` |
| F3 | هیچ `timeout` روی `tick()` نیست — قفل‌شدگی ممکن است | 🟠 | grep خالی |
| F4 | `daily_pnl_pct` منبع مقداردهی در `sarv_router/` نیست | 🟠 | grep خالی |
| F5 | واحد `daily_loss_limit_pct` = ۲.۰ (نه ۳.۰ پرایمر) — پذیرفته یا اصلاح؟ | 🟢 | `config.py:32` |
| F6 | `detect_regime` و `write_gate` بدون try/except در tick | 🟠 | `bot.py:82-88` |
| F7 | `_desired_bots` فقط UPTREND/RANGE را می‌شناسد — DOWNTREND/UNKNOWN → cash | ✅ (خوب) | `bot_lifecycle.py:_desired_bots` |
| F8 | `hydrate_from_state` (Test B) — طراحی دقیق برای بقای restart | ✅ (خوب) | `bot_lifecycle.py:hydrate_from_state` |

---

## ۴. پوشش تست — آنچه دیدم، آنچه ندیدم

**دیدم (test_sarv_router_lifecycle.py، ۱۱۷ خط، ۱۰ تست):**
- first_call_pending، no_switch_before_stability، switch_after_stability، range_switches_to_sarban، unknown_all_cash، downtrend_stops_all، cooldown_blocks_rapid_switch، stability_resets_on_regime_change، no_switch_if_already_active، fail_safe_on_start_error.

**اینها همه مربوط به lifecycle هستند و منطق چرخش را خوب پوشش می‌دهند.** ✅

**ندیدم (و برای تأیید Live نیاز است):**
- ❌ تست kill_switch (manual و auto)
- ❌ تست daily_loss_limit (آستانه، واحد، اثر بر state)
- ❌ تست SIGTERM handler
- ❌ تست `audit.log` روی مسیرهای مختلف
- ❌ تست `hydrate_from_state` از یک state ذخیره‌شده
- ❌ تست رفتار در `start_bot` که بعد از `stop_all` fail شود

**اقدام لازم:** لیست کامل فایل‌های تست SarvRouter را بدهید (بخش ۶) تا یک audit دوم روی آن انجام شود.

---

## ۵. ریسک‌های باقی‌مانده برای Live

| # | ریسک | شدت | مالک |
|---|---|---|---|
| R25 | SIGTERM / graceful shutdown | 🔴 | دی کویر |
| R26 | `expires_at` (معنا + پیاده‌سازی) | 🔴 | دی کویر + دی پرتو |
| R27 | (از handoff پرتو — تعریف دقیق را دی کویر باید بدهد) | ❓ | دی کویر |
| R-New-A | لایه ۱ و ۲ در bot | 🔴 | دی کویر |
| R-New-B | audit gap در manual kill | 🟠 | دی کویر |
| R-New-C | واحد `daily_pnl_pct` تأیید نشده | 🟠 | دی کویر |
| R-New-D | timeout روی tick | 🟠 | دی کویر |

---

## ۶. سؤالات باز (برای دی کویر و حسین)

1. **۱۱ فایل تست ادعایی** — لطفاً `ls -la tests/unit/test_sarv_router_*.py && wc -l` را بدهید تا audit دوم انجام شود.
2. **`daily_pnl_pct`** کجا مقداردهی می‌شود؟ آیا درصد است یا کسری؟
3. **`scheduler.py`** — آیا مستقل از وضعیت کاربر `tick()` را صدا می‌زند؟ (این تعیین می‌کند لایه ۱ و ۲ چقدر حیاتی‌اند.)
4. **`write_gate`** — مقصد کجاست؟ چه کسی آن را می‌خواند؟
5. **معنای دقیق `expires_at`** (R26) چیست؟
6. **آیا ADR رسمی برای ۵ لایه SarvRouter وجود دارد** (طبق M11) یا فقط در کد پیاده شده؟
7. **R27 دقیقاً چیست؟** در SARVBOTS_STATE بدون تعریف آمده.

---

## ۷. قدم‌های بعدی پیشنهادی (اولویت‌بندی)

**پیش‌شرط Live — قبل از هر تغییر دیگر:**
1. افزودن چک لایه ۱ و ۲ در `bot.py` بعد از `store.load()`.
2. پیاده‌سازی SIGTERM handler با audit.
3. رفع audit gap در manual kill.
4. تأیید واحد `daily_pnl_pct` و در صورت لزوم اصلاح مقایسه.
5. تعریف + پیاده‌سازی `expires_at` (R26) با ADR.

**پیش‌شرط کیفیت:**
6. ۶ تست غایب بخش ۴ نوشته شود.
7. `timeout` روی tick.
8. `_safe_stop_all` استثنا را به audit log بفرستد.
9. ADR-چهارم برای ۵ لایه SarvRouter ثبت شود.

**Paper mode:** با وضعیت فعلی، Paper mode بی‌مانع است — فقط برای Live این ۵ مورد بالا لازم است.

---

## ۸. تعهد شاهد

این گزارش فقط بر پایه‌ی خروجی ترمینال ۲۰۲۶-۱۱-۰۹ است. هرجا شاهد نبود، صریح گفتم «غایب» یا «نامعلوم» — نه «احتمالاً». **هیچ ادعایی بدون ارجاع خط/فایل در این سند نیست.** اگر خروجی جدید بیاید که یافته‌ای را نقض کند، این گزارش آپدیت می‌شود (نسخه ۱.۱).

«آهسته، مطمئن، با شاهد، با بازبینی، با مهربانی.»

— **دی دریا**
CTO اکوسیستم سرو پایا
۲۰۲۶-۱۱-۰۹
