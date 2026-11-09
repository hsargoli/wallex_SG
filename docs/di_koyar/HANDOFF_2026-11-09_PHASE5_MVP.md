# 📮 Handoff — Phase 5: Alternative Scenarios (SarvRouter)

> **From:** دی دریا
> **To:** دی کویر
> **Date:** 2026-11-09
> **Scope:** ADR-0044 — Alternatives (MVP)

---

## 1. Summary
Phase 5 (MVP) is complete. Copilot now shows adjacent regime scenarios
with hypothetical risk for each. The MVP is 100% closed.

## 2. Commits (this phase)
- `docs(adr): ADR-0044 Alternative Scenarios (MVP scope)`
- `feat(sarv_router): generate alternative scenarios (ADR-0044 MVP)`
- `feat(frontend): display alternative scenarios (ADR-0044 MVP)`

## 3. What was added
**Backend:**
- `alternatives.py`: `get_adjacent_regimes()`, `generate_alternatives()`
- `bot.py`: `_decision` accepts `alternatives` param; tick populates it
- Tests: 4 new (96 passed total for SarvRouter)

**Frontend:**
- New "سناریوهای جایگزین" card showing adjacent regimes + risk per scenario

## 4. Out of Scope (Future)
- Probability per scenario
- Deep simulation with future candles
- User interaction with scenarios (only display)
