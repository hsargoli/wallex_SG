# 📮 Handoff — Phase 1 Copilot (SarvRouter)

> **From:** دی دریا
> **To:** دی کویر
> **Date:** 2026-11-09
> **Branch:** refactor/full-ddd
> **Scope:** ADR-0039 / ADR-0040 — Phase 1 (بامعنا) — Backend + Frontend

---

## 1. Summary

Phase 1 of "SarvRouter as Copilot" is complete. Each tick now returns a
structured decision with `why`, `evidence`, `confidence`, and `tick_id`.
The decision is persisted in state and passed through API to UI.

No behavioral change to any existing bot. No code in `_archive/` touched.
No changes to `nooaah/`.

---

## 2. Commits

| SHA | Type | Description |
|---|---|---|
| `9bc859a` | docs | ADR-0039 + ADR-0040 + Addendums |
| `5764110` | feat | DecisionReason contract (phase 1a) |
| `ffe09c8` | feat | Uniform evidence across tick paths (phase 1b) |
| `6c25165` | feat | Persist last_decision + API passthrough (phase 1c) |
| `214515b` | feat | Display last Copilot decision in UI (phase 1d) |

---

## 3. Files

**Backend:**
- `backend/app/services/bots/sarv_router/decision.py` — new, 32 lines
- `backend/app/services/bots/sarv_router/bot.py` — +16/-4
- `backend/app/services/bots/sarv_router/store.py` — +1
- `backend/app/presentation/api/v1/sarvrouter.py` — +1
- `backend/tests/unit/test_sarv_router_decision.py` — new, 145 lines

**Frontend:**
- `frontend/app/(app)/sarvrouter/page.tsx` — new card (~60 lines)

**Docs:**
- `docs/adr/0039-sarvrouter-as-copilot.md`
- `docs/adr/0040-copilot-decision-contract.md`
- `docs/di_darya/SARVROUTER_AUDIT_REPORT.md`

---

## 4. Tests

| Stage | Count | Delta |
|---|---|---|
| Baseline (before phase 1) | 71 passed | — |
| After 1a | 73 passed | +2 |
| After 1b | 75 passed | +2 |
| After 1c | 78 passed | +3 |
| After 1d | 78 passed (unchanged) | 0 |

All tests pass. 1 warning (pre-existing StarletteDeprecationWarning).

**Test-First witness:** each backend phase had a gate that verified
"collected → failed → implemented → passed". No code was written before
a failing test existed.

---

## 5. Witnesses

- `py_compile` OK on all modified backend files
- `tsc --noEmit` OK on frontend
- `git diff --stat` showed expected diffs (no surprises)
- 6 total commits in phase 1 (including docs)

---

## 6. What you should verify

**Backend:**
1. `DecisionReason.to_dict()` — preserves old keys + adds Copilot keys?
2. `last_decision` in `SarvState` — does it survive store → load → store?
3. `bot.py` three return paths — all call `self._decision(...)`?
4. API `/status` — returns `last_decision` now?

**Frontend:**
1. New Card visible in `/sarvrouter` — after tick exists, shows `why` + `confidence`?
2. Empty state — when no `last_decision`, shows "منتظر اولین tick"?
3. Persian labels aligned with existing design?

**Test:**
4. `pytest tests/unit/test_sarv_router_decision.py -v` — should show 7 passed.
5. `pytest tests/unit/test_sarv_router_*.py` — should show 78 passed.

---

## 7. Known limitations / Next steps

**Phase 2 (risk) not started.** When we start, we need:
- Source of `fee` / `slip` / `spread` in config
- `RiskProfile` dataclass shape (ADR Addendum needed)
- Display of risk in UI (parallel to confidence)

**Out of scope for this phase (recorded in ADR-0039 Addendum):**
- `proposed_allow_new_entries` — added but not yet consumed by Nooaah
- Gate is still per-system (D-Gate-2, per-user planned 2027-02-09)
- `learn/page.tsx:66` — "24/7 autonomous" text (D-Gate-3)

**If you want to revert:**

git reset --hard 9bc859a~1 # revert to before phase 1
text


But this loses ADR + audit report too. Per-phase revert:
- Just frontend: `git revert <frontend-sha>`
- Just phase 1c: `git revert 6c25165`

---

## 8. Questions for you

1. `confidence` نمایش: درصد (90%) یا خام (0.9)? — I chose percent.
2. `evidence.path` نمایش: فارسی ("چرخه") یا انگلیسی ("lifecycle")? — I chose English (raw).
3. `tick_id` نمایش: ۸ کاراکتر اول یا کامل؟ — I chose 8 (short).

اگر ترجیح متفاوت داری، هر سه در یک commit کوچک قابل تغییرند.

---

— **دی دریا**
2026-11-09
