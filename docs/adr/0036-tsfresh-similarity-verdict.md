# ADR 0036 — tsfresh Similarity Trading Strategy: Verdict = No Edge

- **تاریخ:** 2026-11-07
- **وضعیت:** Proposed
- **نویسنده:** دی برگ (با همکاری حسین، ادامه‌ی کار دی باران)
- **شاهدان:** ۶ backtest پیش‌ثبت‌شده، همه با شاهد قبل/بعد، deterministic

## Context

پس از کار دی باران روی `15_tsfresh_trading_backtest.py` (long-only, TP=4٪/SL=2٪/Fee=0.65٪), شش تست پیش‌ثبت‌شده اجرا شد تا فرضیه‌ی edge بررسی شود.

### نتایج کامل (۶ تست)

| # | Direction | N | Horizon | Trades | WR | PF | MaxDD | Verdict |
|---|---|---|---|---|---|---|---|---|
| baseline | long | 5 | 24h | 2117 | 33.0٪ | 0.58 | −100٪ | FAIL |
| H2 | long | 10 | 24h | 466 | 26.0٪ | 0.42 | −99.6٪ | FAIL |
| H4 | long | 5 | 72h | 4116 | 33.1٪ | 0.58 | −100٪ | FAIL |
| H3 | long | 10 | 72h | 1251 | 31.6٪ | 0.55 | −100٪ | FAIL |
| H5 | **short** | 10 | 24h | 679 | 36.5٪ | 0.68 | −97.9٪ | FAIL |
| H6 | **long-red** | 10 | 24h | 548 | 34.3٪ | 0.63 | −97.3٪ | FAIL |

**Break-even WR** (با TP=4/SL=2/Fee=0.65): **44.2٪**.
همه‌ی تست‌ها **۱۱ تا ۱۸ واحد زیر** break-even.

## Decision

**استراتژی «همه N کندل مشابه سبز → ورود» فاقد edge است. صفر edge، نه ضعیف.**

### فرضیه‌های رد شده

1. ❌ «long-only با N=5 edge دارد» (WR 33.0٪ < 44.2٪)
2. ❌ «سخت‌گیرانه‌تر (N=10) بهتر می‌شود» (بدتر شد: 26-31٪)
3. ❌ «افق 72h هم‌راستا بهتر می‌شود» (بدون تغییر: PF 0.58→0.58)
4. ❌ «سیگنال contrarian است» (short WR 36.5٪، نزدیک random)
5. ❌ «آینه‌ی contrarian (long-red) edge دارد» (WR 34.3٪)
6. ❌ «ترکیب N و horizon اثر دارد» (همه ~33٪)

## Key Insight

در random walk بدون edge، با TP=4/SL=2:

WR_expected = SL / (TP + SL) = 2 / 6 = 33.3٪
text


WR مشاهده‌شده: **26.0٪ تا 36.5٪** (میانگین ~33٪).

⇒ **سیگنال از random walk قابل تشخیص نیست.** اگر edge داشت (هر جهتی)، WR باید >> 44.2٪ می‌رفت. نرفت.

این **قطعی‌ترین نتیجه‌ی ممکن** است: نه «سیگنال ضعیف»، نه «سیگنال بد»، بلکه **«سیگنال = noise»**.

## Consequences

### چه چیزی یاد گرفتیم (درست)

- ✅ **روش scientific:** پیش‌ثبت فرضیه، معیار موفقیت، آرشیو پس از ۶ تست (AP-57, AP-58)
- ✅ **Determinism:** اجرای مکرر = نتیجه‌ی یکسان
- ✅ **گزارش منفی = پیروزی** (AP-39) — 5M سرمایه از ضرر نجات یافت

### Anti-Pattern های جدید (Proposed)

- **AP-65 — pandas 2.x CoW:** `.values` ممکن است read-only باشد → `.to_numpy(dtype=float, copy=True)`. در فایل 15 و 17 این باگ نهفته بود (شانسی کار می‌کرد).
- **AP-66 — Inf cleaning:** `dropna()` فقط NaN حذف می‌کند، نه Inf. `replace([np.inf, -np.inf], np.nan)` قبل از `dropna()` لازم است.
- **AP-67 — label hardcode در گزارش:** `"N<5"` به جای `f"N<{N_MATCHES}"` — گمراه‌کننده بود.

### چه کاری نباید بکنیم

- ❌ **tune دوباره** (p-hacking)
- ❌ «شاید با RSI ترکیب کنیم» — نه، همین تله
- ❌ «شاید تایم‌فریم 4h» — نه
- ❌ **Deploy هیچ‌کدام از این استراتژی‌ها**

### چه کاری باید بکنیم

بازگشت به اولویت‌های ADR-0034:
1. **`human_signal` در Nooaah** (P0)
2. **۵ لایه محافظتی enforcement** (P0)
3. **`sarvban` واقعی** (P1)
4. **UX Builder + Onboarding** (P1/P2)

### تغییر لازم در UI (task جداگانه)

صفحه‌ی `/research/tsfresh` فعلاً فقط baseline (N=5, 24h) را نشان می‌دهد. بهتر است به یک صفحه‌ی «Verdict» ارتقا یابد:
- همه‌ی ۶ تست را نشان دهد
- پیام صریح: «no edge confirmed — analysis only, not a signal»
- مطابق ADR-0034 (Copilot: analysis + reasoning + disclaimer)

## Archive

- `research/tsfresh/17_tsfresh_contrarian_test.py` → `research/_archive/tsfresh/`
- `research/tsfresh/15_tsfresh_trading_backtest.py` → حفظ شد در production (baseline tool برای Copilot page)
- تمام JSON های نتیجه → `research/_archive/tsfresh/results/`
- JSON عمومی → بازگشت به baseline (N=5, 24h)

## منابع

- ADR-0034 (SarvBots = Analysis Platform)
- ADR-0033 (research similarity page)
- AP-39 (گزارش منفی = پیروزی)
- AP-57 (تعریف موفقیت قبل از research)
- AP-58 (N trades < 30 = آمار بی‌معنی)
- V3 دروس ۳۱، ۳۳، ۳۵
