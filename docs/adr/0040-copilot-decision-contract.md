# ADR-0040 — Copilot Decision Contract (DecisionReason)

- **Status:** Proposed
- **Date:** 2026-11-09
- **Author:** دی دریا (CTO)
- **Reviewers:** حسین (رهبر)، دی کویر (مسئول SarvRouter)
- **Related:** ADR-0039 (SarvRouter as Copilot)

---

## 1. Context

`SarvRouter.tick()` در حال حاضر یک `dict` برمیگرداند که مصرفکنندگانش:
- `scheduler.py:last_result`
- `backtest_adapter.py`
- endpoint `sarvrouter.py`
- ۱۱ فایل تست موجود

شکل فعلی: `{"action": str, "regime": str, "active_bots": list, ...}`

برای تبدیل به Copilot (ADR-0039)، هر tick باید **قابل توضیح** باشد:
دلیل، شاهد، اطمینان، و شناسهی قابل ارجاع برای گفتگو (فاز ۳).

## 2. Decision

یک dataclass جدید `DecisionReason` اضافه میشود. شکل `dict` فعلی **حفظ میشود** —
نه شکسته، نه جایگزین. کلیدهای جدید **افزوده** میشوند.

### 2.1. قرارداد

    @dataclass
    class DecisionReason:
        action: str                    # "switched" | "pending" | "no_change" | ...
        why: str                       # فارسی، قابل نمایش به کاربر
        evidence: dict                 # regime, stability, cooldown, gate, capital
        confidence: float              # 0.0-1.0
        tick_id: str                   # شناسه یکتای این tick
        risk: dict | None = None       # فاز ۲
        alternatives: list[dict] = field(default_factory=list)  # فاز ۵

    def to_dict(self) -> dict:
        """شکل قدیمی dict + کلیدهای جدید. سازگار با تست‌های فعلی."""
        ...

### 2.2. سازگاری بازگشتی

- `to_dict()` همان dict فعلی را برمیگرداند، **به‌علاوه** `why`, `evidence`,
  `confidence`, `tick_id`, `risk`, `alternatives`.
- ۱۱ فایل تست موجود بدون تغییر pass می‌شوند (شرط پذیرش این ADR).
- کدهای مصرف‌کننده که فقط `action` می‌خوانند، می‌توانند بی‌تغییر بمانند.

### 2.3. معنای confidence

`confidence` **نه** احتمال سود است، **نه** احتمال موفقیت پیش‌بینی.
معنایش: **«SarvRouter چقدر مطمئن است که این تصمیم، بازتاب شاهدهای همین tick است»**.

- `1.0`: رژیم واحد، پایدار، بدون ابهام
- `0.5`: سیگنال‌های مختلط، multi-tf ناسازگار
- `0.0`: unknown یا خطا

این **خودارزیابی** است، نه پیش‌بینی بازار. تفکیک این دو، بنیادین است — وگرنه
`confidence` به یک وعده‌ی بی‌پشتوانه تبدیل می‌شود.

### 2.4. معنای tick_id

- uuid4 در هر tick
- در `audit.jsonl` ثبت می‌شود
- مصرف‌کننده‌ی اصلی: فاز ۳ (`POST /copilot/why?tick_id=...`)

## 3. Consequences

- `bot.py`: `tick()` اکنون `DecisionReason` برمیگرداند؛ `to_dict()` در مرزهای I/O.
- `audit.py`: `AuditEntry` فیلد `tick_id` می‌گیرد.
- `sarvrouter.py` (API): کلیدهای جدید در پاسخ ظاهر می‌شوند — additive.
- فرانت‌اند: می‌تواند از فاز ۱ `why` و `confidence` را نمایش دهد.
- تست: دو تست جدید اجباری —
  - `test_decision_reason_backward_compatible`
  - `test_decision_reason_to_dict_has_old_keys`

## 4. Open Questions

۱. **tick_id: uuid4 یا sha1(evidence)?**
   - uuid4: یکتا در هر فراخوانی، بدون dedup.
   - sha1: شاهد یکسان → شناسه یکسان، dedup ممکن برای فاز ۳.
   - **پیشنهاد:** uuid4 در فاز ۱؛ اگر فاز ۳ نیاز به dedup داشت، فیلد دوم
     `evidence_hash` اضافه می‌شود (Addendum).

۲. **confidence چطور محاسبه می‌شود؟**
   - فاز ۱: heuristic ساده (مثلاً `0.9` اگر regime تغییر نکرده، `0.5` اگر
     multi-tf ناسازگار).
   - فاز ۲+: calibration از backtest.
   - **پیشنهاد:** heuristic در فاز ۱؛ calibration در ADR جدا.

۳. **evidence: dict آزاد یا dataclass؟**
   - dict: سریع، منعطف، ولی schema-less.
   - dataclass: type-safe، ولی هر تغییر schema نیاز به migration دارد.
   - **پیشنهاد:** dict در فاز ۱؛ اگر فاز ۲ به ساختار دقیق نیاز داشت،
     `Evidence` dataclass در Addendum.

## 5. Witness

این ADR پس از Accepted شدن با سه شاهد پذیرفته می‌شود:
- ۱۱ فایل تست SarvRouter بدون تغییر pass
- تست جدید سازگاری بازگشتی
- یک نمونه خروجی `to_dict()` که هم کلیدهای قدیمی و هم جدید را نشان دهد

---

## Addendum 1.1 — Three Return Paths + Uniform Shape (2026-11-09)

**Status:** Part of ADR-0040 v1.1
**Trigger:** Baseline کد (۲۰۲۶-۱۱-۰۹) نشان داد `tick()` سه مسیر return با شکل‌های متفاوت دارد.
**Approach:** M27 — Addendum.

### A1.1.1. شاهد

`bot.py` سه مسیر return دارد:

| مسیر | خط | کلیدها | `regime` دارد؟ |
|---|---|---|---|
| kill_switch | 59 | `action`, `reason` | ❌ |
| daily_loss_kill | 81 | `action`, `daily_pnl_pct` | ❌ |
| lifecycle (main) | آخر | `action`, `regime`, `active_bots`, ... | ✅ |

مصرف‌کننده‌ها (scheduler.py:80, backtest_adapter.py:19) همه `.get()` استفاده می‌کنند —
پس امروز crash نمی‌شود، ولی `scheduler.py` در حالت kill، `regime=None` لاگ می‌کند.

### A1.1.2. تصمیم: شکل یکنواخت (گزینه Y)

`to_dict()` در همه‌ی مسیرها این پنج کلید Copilot را **همیشه** اضافه می‌کند:

    why, evidence, confidence, tick_id, risk

و در `evidence`، این کلیدها **همیشه** حاضرند (حتی در kill_switch):

    evidence = {
        "action": str,
        "regime": str,         # از state.current_regime در مسیرهای kill
        "reason": str | None,  # kill reason یا None
        "active_bots": list,
        "tick_id": str,
        "path": str,           # "kill_switch" | "daily_loss" | "lifecycle"
    }

**دلیل انتخاب Y:**
- `scheduler.py:80` از این پس `regime` را در همه‌ی مسیرها می‌گیرد (نه `None`).
- فاز ۳ (گفتگو) برای هر `tick_id` می‌تواند دلیل بپرسد، حتی برای kill.
- کلیدهای قدیمی (`reason`, `daily_pnl_pct`) **حذف نمی‌شوند** — فقط `evidence` اضافه می‌شود.

### A1.1.3. آنچه تغییر می‌کند در تست‌ها

- `test_sarv_router_bot.py:test_kill_switch_manual_blocks` — هنوز `r["action"]` را می‌خواند، pass می‌شود.
- `backtest_adapter.py` — هنوز `result.get("action")` را می‌خواند، pass می‌شود.
- تست جدید `test_decision_reason_uniform_shape` — بررسی می‌کند که هر سه مسیر `evidence.regime` دارند.

### A1.1.4. Witness

- Baseline: ۷۱ passed (۲۰۲۶-۱۱-۰۹)
- فایل‌ها: `bot.py:59,81`, `scheduler.py:79-80`, `backtest_adapter.py:17-19`
