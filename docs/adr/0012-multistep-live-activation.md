# 0012. Multi-Step Live Activation

**Status:** Proposed
**Date:** 2026-10-12
**Deciders:** Hosein, Di

## Context

ADR-0011 defined conditions for paper → live. But the activation itself
was a single page with a confirmation phrase. Problem: the user can't
configure the bot's runtime behavior during activation. They enter live
with whatever defaults are hardcoded, and can only change them *after*
going live (via /config PUT).

For a financial operation, activation should be a **wizard** where the
user commits the bot's full configuration step-by-step, with clear
review at each step.

Also: kill-switch must be **instant, no confirmation**. A user who wants
to stop the bot (or someone else's money on the bot) needs one click.

## Decision

**1. Multi-step activation wizard (6 steps):**

| Step | Title | Config set |
|---|---|---|
| 1 | Review | (display only — paper performance, warnings) |
| 2 | Strategy | min_confidence, confirmation_candles, tp_atr_mult, sl_atr_mult, volume_z_min |
| 3 | Position Mgmt | max_concurrent_positions, top_n |
| 4 | Capital | capital_total (from wallet) |
| 5 | Risk | daily_loss_limit_pct |
| 6 | Confirm | typed phrase + activate |

Each step: user enters values → Next validates → state saved partially
(so user can resume if they leave).

**2. Runtime config persisted in state:**

    NooaahState.runtime_config: dict[str, Any]
    {
        "min_confidence": 85,
        "confirmation_candles": 2,
        "tp_atr_mult": 3.0,
        "sl_atr_mult": 1.5,
        "volume_z_min": -0.5,
        "max_concurrent_positions": 1,
        "top_n": 5,
        "capital_total": 5_000_000,
        "daily_loss_limit_pct": 2.0,
    }

Scheduler reads runtime_config (not hardcoded NooaahConfig).

**3. Kill-switch: no confirmation, one click.**

- UI: single button, no confirm dialog
- Backend: `/kill` already exists; removed UI friction only
- Also: no keyboard shortcut required; mouse click is enough

**4. Activation endpoints:**

- `GET  /v1/nooaah/live/draft` — current partial config
- `PUT  /v1/nooaah/live/draft` — save a step (partial)
- `POST /v1/nooaah/live/activate` — already exists (requires draft complete + phrase)

The `draft` is separate from `runtime_config`; only merged into
runtime_config at activate.

**5. UI wizard:**

- `/nooaah/live/activate` becomes a wizard with:
  - Progress bar (Step N of 6)
  - Back / Next buttons
  - Per-step validation
  - Review summary at final step before activation

## Consequences

**Positive:**
- User explicitly configures everything before committing
- Partial save allows resume if interrupted
- Kill-switch is instant (safety)
- Scheduler uses runtime_config (not hardcoded)

**Negative:**
- More complex UI (wizard vs single page)
- Draft state added to NooaahState
- More endpoints

**Neutral:**
- Wizard is the primary path; direct `/config` PUT still exists for
  adjustments after live.

## Alternatives Considered

**Single-page activation with optional advanced section (rejected):**
doesn't force user to think about each parameter.

**Lock defaults, no configuration (rejected):** users have different
risk profiles.

**Separate config page, then activate (rejected):** two places; wizard
combines them.

## Risks

- **Wizard fatigue:** 6 steps may feel long. Mitigation: short forms,
  defaults pre-filled.
- **Partial save inconsistency:** if user changes step 2 after setting
  step 3, must re-validate. Mitigation: validate all on activate.
- **Kill without confirmation:** user might click accidentally.
  Mitigation: position far from other buttons; visual distinction.

## Future Work

- Save multiple named configurations (presets)
- Import/export config as JSON
- Audit log of activation events

## References

- ADR-0010 — Live Trading Architecture
- ADR-0011 — Live Activation Process
