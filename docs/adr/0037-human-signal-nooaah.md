# ADR 0037 — HumanSignal in Nooaah (Safety Filter, Not ML Replacement)

- **تاریخ:** 2026-11-07
- **وضعیت:** Proposed
- **نویسنده:** دی برگ (بر اساس طرح دی پرتو + شاهد)
- **بازبین:** دی پرتو (async — بعد از commit)
- **شاهدان:** بلاک خواندن 2026-11-07

## Context

### وضعیت فعلی (شاهد)

1. **bear_hunter آرشیو شده** — مسیر واقعی: `app/services/bots/_archive/bear_hunter/`. نامه‌ی دی پرتو به مسیر قدیمی ارجاع داده بود.
2. **HumanSignal در bear_hunter پیاده‌سازی شده** — frozen dataclass با ۵ فیلد + `set_signal` با validation.
3. **Nooaah فاقد HumanSignal است** — grep = RC=1.
4. **NooaahState** فیلدهای `daily_loss_limit_pct`, `kill_switch`, `live_stage`, `daily_loss_hit`, `cooldown_until`, `killed` دارد — هیچ فیلد human_signal.
5. **`run_cycle(entries_allowed: bool = True)`** — SarvRouter gate را مصرف می‌کند (`data/sarv_router/gate.json`). `entries_allowed=False` → exits only.
6. **Nooaah API** — `/config`, `/kill`, `/resume`, `/readiness`, `/live/activate`, `/live/pause`, `/live/stage/advance`, `/status`, `/cycles`, `/backtest`. هیچ endpoint human_signal.
7. **Nooaah tests** — فقط ۱ فایل: `test_nooaah_strategy.py`.
8. **بدهی فنی مجزا:** `live_bot.py` به `_archive.bear_hunter` import می‌کند (خطوط ۱۴-۱۶). خارج از scope (خط سرخ ۳) — ADR-0038 جدا.

### چرا این ADR؟

حسین و دی پرتو تأیید کردند: HumanSignal در Nooaah پیاده‌سازی شود — حالت ۱ (فیلتر ایمنی)، نه حالت ۲ (جایگزین ML).

**دلیل (شاهد):** Nooaah تنها ربات ML-based و سودده است (PF=۱.۳۲ در Q4-2023). HumanSignal فقط veto می‌کند — نه دستور می‌دهد. ML همچنان تصمیم‌گیرنده‌ی اصلی است.

## Decision

### ۱. دو فیلد ساده در NooaahState

    human_direction: str = "neutral"   # "bearish" | "bullish" | "neutral"
    human_expires_at: int = 0          # unix timestamp; 0 = never expires

نه کلاس کامل HumanSignal — طبق خط سرخ ۱.

### ۲. Helper — حالت ۱

    @property
    def human_blocks_entry(self) -> bool:
        """True فقط اگر human_direction == 'bearish' و signal منقضی نشده."""
        if self.human_direction != "bearish":
            return False
        if self.human_expires_at == 0:
            return True
        return int(time.time()) < self.human_expires_at

### ۳. Veto در run_cycle (بعد از SarvRouter gate)

    if not entries_allowed:
        return "exits_only"

    if self._state.human_blocks_entry:   # ← جدید
        return self._log_and_summarize(
            ..., status="blocked_by_human", action="blocked_by_human",
            reason_fa="سیگنال انسانی: bearish — ورود جدید ممنوع",
            closed=closed,
        )

### ۴. جدول رفتار

| سناریو | رفتار |
|---|---|
| human_direction = "bullish" | هیچ (ML تصمیم می‌گیرد) |
| human_direction = "neutral" | هیچ |
| human_direction = "bearish" (معتبر) | ورود ممنوع؛ مدیریت پوزیشن‌ها همچنان |
| human_direction = "bearish" (منقضی) | ورود آزاد |
| پوزیشن باز + تغییر به bearish | هیچ پوزیشنی بسته نمی‌شود (ADR-0020 §5) |

### ۵. Legacy state (backward compat)

NooaahState.load(): نبودِ human_direction → "neutral". نبودِ human_expires_at → 0.

## Consequences

### مثبت
- فیلتر ایمنی، نه جایگزین ML — edge حفظ می‌شود
- ۲ فیلد ساده — refactor کوچک (۱-۲ روز)
- هم‌راستا با ۵ لایه محافظتی (V3 §18)
- بدون تغییر در bear_hunter (خط سرخ ۳)
- موازی با SarvRouter gate (دو فیلتر مستقل)

### منفی
- یک state field جدید + serialization
- یک API endpoint جدید + helper
- ۶ تست جدید

## ۴ خط سرخ (از نامه‌ی دی پرتو)

1. ۲ فیلد ساده، نه کلاس کامل
2. حالت ۱ (فیلتر ایمنی)، نه جایگزین ML
3. هیچ تغییری در bear_hunter
4. Test-First

## Test Plan (۶ تست، ۵ state-level + ۱ integration)

| # | تست | انتظار |
|---|---|---|
| ۱ | test_default_state_no_block | neutral + no expiry → False |
| ۲ | test_human_bearish_blocks_entry | bearish + no expiry → True |
| ۳ | test_human_neutral_does_not_block | neutral → False |
| ۴ | test_human_bullish_does_not_block | bullish → False (mode 1) |
| ۵ | test_human_expired_signal_ignored | bearish + expired → False |
| ۶ | test_human_bearish_vetoes_ml_entry | integration: run_cycle با bearish → action=blocked_by_human |

## Implementation Steps (~۱-۲ ساعت چون refactor کوچیکه)

1. ۵ تست state-level RED (این commit)
2. افزودن ۲ فیلد + helper به NooaahState + save/load
3. اجرای ۵ تست → GREEN
4. تست integration RED → GREEN (veto در run_cycle)
5. API endpoint (POST/GET /nooaah/human-signal)
6. Regression — pytest کامل

## بدهی فنی مرتبط (خارج از scope)

live_bot.py → _archive.bear_hunter (خطوط ۱۴-۱۶). ADR-0038 (Proposed) — جداگانه.

## منابع

- ADR-0020 (Human-in-the-Loop Signal) — reference
- ADR-0034 (SarvBots = Analysis Platform)
- V3 §18 (5 لایه محافظتی)
- نامه‌ی دی پرتو (2026-11-07) — تصمیم معماری
- شاهد بلاک خواندن 2026-11-07 — مسیرهای واقعی
