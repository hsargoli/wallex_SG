# ADR-0041 — Risk Profile (Phase 2 Copilot)

- **Status:** Proposed
- **Date:** 2026-11-09
- **Author:** دی دریا (CTO)
- **Reviewers:** حسین (رهبر), دی کویر (مسئول SarvRouter)
- **Related:** ADR-0039 (Copilot), ADR-0040 (Decision Contract)

---

## 1. Context

فاز ۱ (بامعنا) کامل شد: هر tick `why`, `evidence`, `confidence`, `tick_id` دارد.
ADR-0040 فیلد `risk: dict | None` را در `DecisionReason` رزرو کرد، ولی خالی ماند.

فاز ۲ می‌خواهد این فیلد را پر کند تا Copilot بگوید:
«این پیشنهاد، با fee، slippage، و spread، تقریباً X تومان هزینه دارد.»

**شاهد از کد (۲۰۲۶-۱۱-۰۹):**
- `SarvRouterConfig` هیچ فیلد `fee_pct` / `slippage_pct` / `spread_pct` ندارد.
- fee فقط در `_archive/` هست (bear_hunter: `entry_fee_pct=0.2`).
- `backtest_adapter.run_sarv_backtest` هیچ هزینه‌ای محاسبه نمی‌کند.

## 2. Decision

`RiskProfile` به عنوان dataclass در `decision.py` اضافه می‌شود.

### 2.1. مقادیر پیش‌فرض (محافظه‌کارانه)

    fee_pct: float = 0.2
    slippage_pct: float = 0.1
    spread_pct: float = 0.05

اینها از درس پرایمر (Fee ۰.۲٪ × ۲) و تجربه bear_hunter. هیچ‌کدام از backtest کالیبره نشده.

### 2.2. ساختار RiskProfile

    @dataclass(frozen=True)
    class RiskProfile:
        fee_pct: float
        slippage_pct: float
        spread_pct: float
        estimated_cost_pct: float
        capital_at_risk_tmn: float
        estimated_cost_tmn: float
        is_hypothetical: bool

        def to_dict(self) -> dict: ...

### 2.3. چه زمانی پر می‌شود؟

(در Addendum 1.1 بازنگری شد — پایین را ببینید.)

## 3. Consequences

- `config.py`: سه فیلد جدید
- `decision.py`: `RiskProfile` dataclass
- `bot.py`: در مسیرهای مختلف `risk` پر یا None
- API: `risk` در `last_decision` ظاهر می‌شود
- UI: در فاز ۲ب، `risk` نمایش داده می‌شود

## 4. Open Questions

۱. slippage و spread — تخمینی یا اندازه‌گیری‌شده؟
۲. نمایش در UI — درصد یا تومان؟
۳. آیا `RiskProfile` در audit هم ثبت شود؟

## 5. Witness

پذیرش با سه تست اولیه + پنج تست Addendum 1.1.

---


---

## Addendum 1.1 — Hypothetical Risk in All Paths (2026-11-09)

**Status:** Part of ADR-0041 v1.1
**Trigger:** تصمیم حسین — Copilot باید «هزینه‌ی فرضی» را حتی در حالت‌های pending/no_change نشان دهد.
**Approach:** M27 — Addendum.

### A1.1.1. تصحیح بند 2.3

**متن قبلی (v1.0، اکنون باطل):**
> «risk فقط در مسیر switched پر می‌شود؛ در سایر مسیرها risk = None.»

**متن جایگزین (v1.1):**

| مسیر | `risk` | `is_hypothetical` | توضیح |
|---|---|---|---|
| `switched` | پر | `False` | ورود واقعی در حال انجام است |
| `pending` | پر | `True` | «اگر همین الان وارد می‌شدیم، هزینه X» |
| `no_change` | پر | `True` | «اگر ورود جدید انجام می‌شد، هزینه X» |
| `kill_switch_active` | `None` | — | سیستم متوقف است — سناریوی فرضی معنا ندارد |
| `daily_loss_kill` | `None` | — | همان |

### A1.1.2. RiskProfile نسخه v1.1

    @dataclass(frozen=True)
    class RiskProfile:
        fee_pct: float                   # هر طرف
        slippage_pct: float
        spread_pct: float
        estimated_cost_pct: float        # 2*fee + slip + spread (رفت و برگشت)
        capital_at_risk_tmn: float       # واقعی یا فرضی
        estimated_cost_tmn: float        # capital * cost_pct / 100
        is_hypothetical: bool            # True برای pending/no_change

### A1.1.3. محاسبه‌ی capital_at_risk در مسیرهای فرضی

- در `switched`: از `state.allocations` که `allocate_capital` ساخته — همان مقدار واقعی.
- در `pending` و `no_change`: تابع `allocate_capital(state.total_capital, regime, config)`
  یک‌بار صدا زده می‌شود تا **بدانیم اگر تصمیم همین حالا گرفته می‌شد، چقدر سرمایه درگیر می‌شد**.
  این یک محاسبه‌ی خالص است (بدون side-effect روی state). فقط برای نمایش.

**توجه:** این محاسبه **هیچ تغییر رفتاری** ایجاد نمی‌کند. lifecycle همچنان همان‌طور که الان کار می‌کند، تصمیم می‌گیرد.
`allocate_capital` در pending یک فراخوانی خالص است که فقط output آن را در risk می‌گذاریم و دور می‌ریزیم.

### A1.1.4. نمایش در UI (فاز ۲ب)

- بج `is_hypothetical=True`: عنوان «هزینه‌ی فرضی (اگر وارد شویم)» — رنگ خاکستری/خنثی.
- بج `is_hypothetical=False`: عنوان «هزینه‌ی پیشنهادی» — رنگ آبی/فعال.
- در هر دو: `estimated_cost_pct` با دو رقم اعشار + `estimated_cost_tmn` با جداکننده‌ی هزارگان.

### A1.1.5. Open Questions جدید

۱. **در `pending`، allocation بر اساس regime فعلی است یا regime مطلوب؟**
   - پیشنهاد: regime فعلی (همان که `detect_regime` برگرداند).
   - دلیل: این همان رژیمی است که اگر تثبیت شود، مبنای تصمیم می‌شود.

۲. **آیا `is_hypothetical` باید در audit هم ثبت شود؟**
   - بله، برای بازبینی بعدی: «چند بار هزینه‌ی فرضی نشان داده شد».

۳. **آیا `fee_pct` را باید از config Wallex بگیریم؟**
   - خارج از محدوده‌ی فاز ۲. ثابت‌های محافظه‌کارانه کافی‌اند.

### A1.1.6. Witness

پذیرش این Addendum با پنج تست جدید:
- `test_risk_profile_basic_math` — محاسبه‌ی درست `estimated_cost_pct` و `_tmn`
- `test_risk_none_in_kill_switch` — در مسیر kill، `risk is None`
- `test_risk_hypothetical_in_pending` — در pending، `is_hypothetical=True`
- `test_risk_real_in_switched` — در switched، `is_hypothetical=False`
- `test_risk_capital_matches_allocation` — `capital_at_risk_tmn` با allocations همگام است
