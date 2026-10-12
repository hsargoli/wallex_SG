# 0011. Live Activation Process

**Status:** Proposed
**Date:** 2026-10-12
**Deciders:** Hosein, Di

## Context

ADR-0010 introduced live trading with a `mode: paper | live` toggle.
Problem: switching from paper to live with one click is too easy for a
financial operation that involves real money. It doesn't force
evaluation, doesn't record evidence, and doesn't have progressive
safety.

We need a **process**, not a toggle: multi-step, evidence-based,
staged.

## Decision

**1. State machine (replaces simple mode):**

    paper-testing  ──[6 conditions met]──▶  ready-for-live
    ready-for-live ──[typed confirmation]──▶ live-active
    live-active    ──[kill or auto-pause]──▶ live-paused
    live-paused    ──[user resume]──▶ live-active

**2. Conditions for paper-testing → ready-for-live:**

Must ALL be true over the last 7 days:
- ≥ 7 days in paper mode
- ≥ 10 trades executed
- Win rate ≥ 40%
- Paper return > 0%
- kill-switch activations: 0
- daily-loss-limit hits: 0

Until all are met, "Activate Live" button is disabled.

**3. Activation flow (when conditions met):**

- UI shows paper performance summary (7d)
- Hard warning: "پول واقعی — برگشت‌ناپذیر"
- User types the phrase "با مسئولیت خودم" in a text field
  (not just a checkbox)
- POST /v1/nooaah/live/activate with the typed phrase
- Backend validates phrase + readiness; transitions state

**4. Staged capital rollout:**

| Stage | Condition to advance | Max capital |
|---|---|---|
| 1st (initial live) | 5 winning trades | 10% of wallet |
| 2nd | 10 winning trades + Sharpe ≥ 0.3 | 30% |
| full | 20 winning trades | 100% |

Capital cap enforced server-side; user cannot set higher until
conditions met.

**5. Auto-pause conditions (bot pauses itself, requires user resume):**

- daily loss limit hit (existing)
- 3 consecutive losing trades
- any error from Wallex on order placement
- balance drift > 5% (state vs actual Wallex)

First 24h of live: also pause on any single loss > 1%.

**6. State persistence:**

Extended NooaahState:
- `mode` (string): one of the 4 states
- `activated_live_at` (int): unix timestamp
- `paper_started_at` (int)
- `consecutive_losses` (int)
- `live_stage` (int): 1, 2, or 3
- `pause_reason` (str | None)

## Consequences

**Positive:**
- Forces evidence-based decision (not emotional)
- Progressive capital rollout limits damage
- Auto-pause catches anomalies early
- Typed confirmation prevents accidental clicks

**Negative:**
- More complex UI (readiness checklist + modal)
- Backend state grows
- More endpoints to maintain

**Neutral:**
- paper-testing duration is ~1 week minimum (calendar time)

## Alternatives Considered

**Simple toggle (rejected):** too easy, no evidence, no staged rollout.

**Password prompt (rejected):** doesn't force evaluation of results.

**No staged rollout (rejected):** 100% capital on first live order is
reckless.

## Risks

- **Overly-strict conditions:** 7 days may feel long if market is slow.
  Mitigation: conditions are configurable; user can see progress.
- **Auto-pause false positives:** 3 consecutive losses may trigger in
  normal variance. Mitigation: require user resume, not automatic
  restart.
- **Typed phrase as security theater:** it's not a password, just a
  speed bump. Acceptable for MVP; real 2FA in Phase 5 (auth).

## Future Work

- 2FA for activation (Phase 5, with auth)
- Email/Telegram notification on state transitions
- Live performance dashboard (win rate, Sharpe, DD over time)

## References

- ADR-0010 — Live Trading Architecture
- ADR-0001 — Live Trading Default
- docs/nooaah_ideas.md — 18 tested ideas
