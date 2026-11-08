# ADR 0034 — SarvBots: Analysis Platform, Not Autopilot

- **تاریخ:** 2026-11-04
- **وضعیت:** Accepted
- **نویسنده:** دی باران (با همکاری حسین، دی پرتو، دی دریا)
- **شاهدان:** Investigate امروز + verdict Nooaah backtest

## Context

### چه شد که به این تصمیم رسیدیم؟

امروز (2026-11-04) بعد از ۲ ساعت tuning Nooaah verdict صریح آمد:

| تست | WR | PF | نتیجه |
|---|---|---|---|
| Nooaah default (conf=85) | 36.3٪ | 0.77 | ❌ زیان‌ده |
| Nooaah tuned (conf=95) | 39.2٪ | 0.91 | ❌ هنوز زیان‌ده |
| Nooaah gated (SarvRouter uptrend) | 39.2٪ | 0.91 | ❌ بدون بهبود |
| SarvRouter standalone | — | — | ✅ 240 switch، 0 kill |

**⇒ نتیجه:** «تله ربات پول‌درار» واقعی است. هیچ رباتی همیشه سود نمی‌دهد.
حتی Medallion Fund (بهترین صندوق تاریخ) ۳۴٪ اشتباه می‌کند.

### چرا این ADR؟

حسین (رهبر) vision را صریح کرد:
> «سروباتس باید گردآورنده ربات‌های تحلیلی باشد. ربات‌هایی که تصمیم‌گیری را آسان می‌کنند. اما تصمیم‌گیرنده نهایی انسان است. سروباتس یک پلتفرم برای بهتر کردن است.»

Investigatte امروز نشان داد این vision **قبلاً در DNA پروژه هست، ولی پراکنده**:

| DNA (در کد/سند) | شکاف (پیاده‌سازی) |
|---|---|
| ADR-0020 (HumanSignal) — Accepted | ❌ در Nooaah پیاده نشده |
| ۵ لایه محافظتی در `user_bot_config.py` | ❌ در SarvRouter/Nooaah اعمال نمی‌شود |
| `gate.json` (allow_new_entries) | ✅ هست، ولی فقط از SarvRouter |
| `sarvban` در SarvRouter config | ❌ ربات وجود ندارد (placeholder) |
| `tsfresh similarity page` (تحلیل) | ✅ هست، ولی static JSON (بدون API) |

**⇒ تصمیم: یکپارچه‌سازی این DNA در یک ADR + roadmap اجرایی.**

## Decision

**سروباتس، پلتفرم گردآورنده‌ی ربات‌های تحلیلی است، نه ربات‌های معامله‌گر خودکار.**

### چهار اصل

#### ۱. Bot = Analysis + Suggestion (نه Decision)
هر ربات باید:
- تحلیل ارائه دهد (نه فقط سیگنال)
- Reasoning داشته باشد (چرا؟)
- Confidence + Sample Size داشته باشد
- Disclaimer: «نه سیگنال معاملاتی»

مثال: `tsfresh similarity page` (دیروز) — الگو + forward return + confidence + sample size، نه «بخر».

#### ۲. Human = Final Decision (همه اقدامات با gate)
- هر سفارش: `is_trading_enabled=True` + `live_stage` کافی
- `human_signal` (طبق ADR-0020) در همه‌ی ربات‌ها
- `kill_switch` per-user قابل اجرا توسط انسان
- **هیچ رباتی نباید بدون gate انسانی، trade کند.**

#### ۳. Learning = Shared (ربات پیشنهاد، انسان تأیید)
- ربات پیشنهاد tuning می‌دهد (با شاهد)
- انسان تأیید/رد می‌کند
- Override انسان، ثبت و برای بهبود ربات استفاده شود
- **❌ Auto-tune در Live ممنوع** — فقط Paper mode

#### ۴. Robustness > Profit (اشتباه‌پذیری کران‌دار)
معیار موفقیت ربات:
- ✅ «بزرگ‌ترین ضرر یک روز؟» (نه «چقدر سود؟»)
- ✅ «اگر ۱۰ بار باخت، چه می‌شود؟» (drawdown sequence)
- ✅ «رفتار در رژیم جدید (که ندید)؟» (out-of-sample robustness)
- ❌ «PF > 1.5 در backtest» (overfit risk)

SarvRouter دقیقاً همین کرد: ۰ kill، ۲۴۰ switch منظم، cash min 400K (نه ۰).

## Consequences

### چه چیزهایی باید ساخته شود (roadmap)

| # | کار | اولویت | زمان |
|---|---|---|---|
| ۱ | **`human_signal` در Nooaah** (طبق ADR-0020) | P0 | ۱-۲ روز |
| ۲ | **۵ لایه محافظتی enforcement** در SarvRouter/Nooaah | P0 | ۲-۳ روز |
| ۳ | **`sarvban` واقعی** (range bot — placeholder است) | P1 | ۲-۳ روز |
| ۴ | **UI human_signal** (override + reasoning) | P1 | ۲-۳ روز |
| ۵ | **API `/v1/research/tsfresh`** (به‌جای static JSON) | P2 | ۱-۲ روز |
| ۶ | **Learning loop** (override human → tuning پیشنهاد) | P2 | ۳-۵ روز |

### Anti-Patterns (ممنوع)

- ❌ ربات Autopilot (بدون gate انسانی)
- ❌ وعده‌ی سود بدون reasoning + confidence + sample size
- ❌ Auto-tune در Live (بدون تأیید انسان)
- ❌ Backtest-only verdict (بدون Paper mode ۳۰ روز)
- ❌ رباتی که «چرا» را توضیح نمی‌دهد

### ربات‌های آینده: باید Analysis-first باشند

✅ **نمونه‌های درست:**
- `tsfresh similarity` (ابزار تحلیل، نه سیگنال)
- `Nooaah` (پیشنهاددهنده، با human_signal — بعد از پیاده‌سازی)
- `Sarvban` (range analyzer، نه معامله‌گر خودکار)

❌ **نمونه‌های ممنوع:**
- «ربات سودده ۱۰۰٪» (تله)
- «Auto-trade با AI» (بدون gate)

## منابع

- ADR-0020 (HumanSignal) — هست، پیاده‌سازی ناقص
- Primer V4 — ۵ لایه محافظتی (بخش ۱۸)
- Investigate 2026-11-04 (۴ شکاف)
- Verdict Nooaah (PF 0.77 → 0.91، هنوز زیان‌ده)

## تاریخچه

- 2026-11-04: نوشته شد (پس از Investigate + verdict Nooaah)


---

## Addendum (2026-11-08) — bear_hunter Legacy Cleanup

پس از ADR-0038، وضعیت به‌روز شده:

- **`bear_hunter` آرشیو شده** (`_archive/bear_hunter/`) — از ۲۰۲۶-۱۰-۱۸
- **صفحه `/bear-hunter` حذف شد** — ۲۰۲۶-۱۱-۰۸ (ADR-0038 phase 2)
- **`live_bot.py` + `specialized_backtest.py` حذف شدند** — ۲۰۲۶-۱۱-۰۸ (ADR-0038 phase 1)
- **`/backtest` بدون بخش specialized** — فقط main backtest (سالم، endpointهای `/v1/backtest/*`)
- **Nooaah تنها ربات فعال و قابل استفاده** است (`/nooaah/*`)

این Addendum، تناقض Context ADR-0034 («Nooaah تنها ربات ML-based و سودده») با واقعیت قبلی (bear_hunter در sidebar فعال) را رفع می‌کند.

**شاهدان:** ADR-0038، شاهد ترافیک nginx (۰ API call)، DB check (۰ user با trade_token)، git log (۲۰ روز بدون کامیت bear_hunter).

**Refs:** ADR-0038 (bear_hunter legacy cleanup).
