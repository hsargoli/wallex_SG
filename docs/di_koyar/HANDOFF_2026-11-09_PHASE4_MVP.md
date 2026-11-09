# 📮 Handoff — Phase 4: Feedback Loop (SarvRouter)

> **From:** دی دریا
> **To:** دی کویر
> **Date:** 2026-11-09
> **Scope:** ADR-0043 — Feedback Collection (MVP)

---

## 1. Summary
Phase 4 (MVP) is complete. Users can now click "Accept" or "Reject" on the last Copilot decision.
This feedback is saved to a `feedback.jsonl` file for future analysis.

## 2. Commits
- `feat(sarv_router): FeedbackTrail + /feedback endpoint (ADR-0043 MVP)`
- `feat(frontend): add feedback accept/reject buttons (ADR-0043 MVP)`

## 3. What was added
**Backend:**
- `feedback.py`: `FeedbackTrail` and `FeedbackEntry`.
- `sarvrouter.py`: `POST /feedback` endpoint (validates tick_id, writes JSONL).
- Tests: 7 new.

**Frontend:**
- `lib/api.ts` & `lib/queries.ts`: API method and mutation hook.
- `page.tsx`: Accept/Reject buttons + success/error message.

## 4. Out of Scope (Future)
- Aggregating feedback to adjust confidence.
- Storing feedback for historical ticks (only `last_decision` is supported).
