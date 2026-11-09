# 📮 Handoff — Phase 2: Risk Awareness (SarvRouter)

> **From:** دی دریا
> **To:** دی کویر
> **Date:** 2026-11-09
> **Branch:** refactor/full-ddd
> **Scope:** ADR-0041 — Phase 2 (آگاهی از ریسک)

---

## 1. Summary

Phase 2 of "SarvRouter as Copilot" is complete.
Copilot now estimates the cost of entry (fee, slippage, spread) and
shows it to the user. It does this **even in pending/no_change states**
as a hypothetical scenario (is_hypothetical=True).

No behavioral changes. No autonomous actions. Just more transparency.

---

## 2. Commits

- `feat(sarv_router): RiskProfile with hypothetical mode (ADR-0041 phase 2)`
- `feat(frontend): display risk analysis (ADR-0041 phase 2b)`

---

## 3. What was added

**Backend:**
- `SarvRouterConfig`: `fee_pct=0.2`, `slippage_pct=0.1`, `spread_pct=0.05`
- `decision.py`: `RiskProfile` dataclass with `to_dict()`
- `bot.py`: `_make_risk()` calculates `2*fee + slip + spread`
  - Applied to `switched` (is_hypothetical=False)
  - Applied to `pending/no_change/cooldown` (is_hypothetical=True)

**Frontend:**
- New card "تحلیل ریسک" after the Copilot decision card
- Shows `estimated_cost_pct`, `estimated_cost_tmn`, `capital_at_risk_tmn`
- Badge changes color if `is_hypothetical` is True vs False

**Tests:**
- 5 new tests for RiskProfile (83 total passed)

---

## 4. What you should verify

1. `pytest tests/unit/test_sarv_router_*.py -q` → expect 83 passed.
2. `npx tsc --noEmit` → clean.
3. Look at `/sarvrouter` page: the new Risk card should appear
   once a `last_decision` is present.

---

## 5. Open questions (same as ADR-0041 Addendum)

- Are the fee/slip/spread defaults correct for Wallex?
- Should `is_hypothetical` be logged in audit?
