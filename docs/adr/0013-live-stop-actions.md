# 0013. Live Stop Actions

**Status:** Proposed
**Date:** 2026-10-12
**Deciders:** Hosein, Di

## Context

ADR-0011/0012 introduced live activation. But "stop" was a single
action: set killed flag → positions stay open. Problem: user can't
choose what happens to open positions. Sometimes they want the bot to
close everything; sometimes they want to keep positions and manage
manually; sometimes they want a hard kill.

Also: the cooldown after daily-loss was "until end of UTC day" — could
be up to 24h. Too long for a single loss event.

## Decision

**1. Three explicit stop actions (user chooses):**

**a. SELL** — market sell all positions at best bid, return capital
to `capital_available`, transition to `live-paused`. Resumable.

**b. PAUSE** — keep positions open, transition to `live-paused`.
Bot stops managing positions (no TP/SL). Resumable — user may change
their mind and resume.

**c. KILL** — keep positions open, transition to `killed` (via
`live-paused`). **Non-resumable**: user must reset state manually to
re-enable the bot.

**2. Stop preview endpoint (read-only):**

Before choosing an action, UI calls `GET /live/stop/preview` which
returns each position's current best_bid, last_price, PnL (%). No
state change.

**3. Best bid for sells:**

Market sells use `best_bid` from order book (not `last_price`) because
that's what a seller will actually get. Fallback to `last_price` if
order book fetch fails.

**4. Cooldown after daily loss: 6 hours (not full day).**

Replaces `daily_loss_hit` which previously blocked until UTC midnight.
Now: when daily loss limit is reached, enter cooldown for 6 hours.
After 6h, bot resumes automatically (state not killed).

## Consequences

**Positive:**
- User has full control at stop time
- Preview gives decision support (current PnL visible)
- KILL vs PAUSE distinction prevents accidental loss of state
- 6h cooldown fits intraday recovery; not overly punitive

**Negative:**
- Market sell at bid = small slippage (bid < last_price)
- Three buttons = more UI decision-making at a stressful moment
- Partial sell failure (Wallex error): position stays open, needs retry

**Neutral:**
- KILL requires manual reset (documented in UI)

## Alternatives Considered

**Single stop (set killed only):** rejected — user couldn't choose.

**Auto-sell always:** rejected — user may want to hold positions.

**Full-day cooldown:** rejected — too restrictive.

## Risks

- **Market sell price slippage:** on thin books, bid may be far from
  last_price. Mitigation: preview shows the exact bid before user
  confirms.
- **Sell failure:** if Wallex errors mid-sell, some positions close,
  some stay open. State must handle partial completion. Mitigation:
  log per-position; `capital_available` reflects what actually sold.
- **KILL not understood as non-resumable:** user clicks kill expecting
  to resume later. Mitigation: UI shows explicit warning before KILL.

## References

- ADR-0011 — Live Activation Process
- ADR-0012 — Multi-Step Live Activation
