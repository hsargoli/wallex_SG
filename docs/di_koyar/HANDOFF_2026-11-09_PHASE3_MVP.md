# 📮 Handoff — Phase 3: Conversation MVP (SarvRouter)

> **From:** دی دریا
> **To:** دی کویر
> **Date:** 2026-11-09
> **Scope:** ADR-0042 — Conversation Engine (MVP)

---

## 1. Summary
Phase 3 (MVP) is complete. The Copilot can now answer "Why?" about its last decision.
To keep the MVP lightweight, we only read from `last_decision` (no historical JSONL).

## 2. Commits
- `feat(sarv_router): ConversationEngine + /why endpoint (ADR-0042 MVP)`
- `feat(frontend): add Why? button for conversation MVP (ADR-0042)`

## 3. What was added
**Backend:**
- `conversation.py`: `ConversationEngine.explain()` (Rule-based).
- `sarvrouter.py`: `GET /why` endpoint.
- Tests: 5 new (88 total).

**Frontend:**
- `lib/api.ts`: `getSarvRouterWhy()` method.
- `lib/queries.ts`: `useSarvRouterWhy()` hook.
- `page.tsx`: "چرا؟" button + text box for the answer.

## 4. Out of Scope (Future)
- Full history.
- LLM integration.
