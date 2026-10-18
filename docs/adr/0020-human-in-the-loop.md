# 0020. Human-in-the-Loop Signal + Lending Capacity

**Status:** Accepted
**Date:** 2026-10-18
**Deciders:** Hosein, Di (Sahara), Di (Darya)

## Context

Phase 0 of bear_hunter introduced a HumanSignal dataclass that replaces the old current_regime field with an explicit user-set direction. This ADR formalizes that design and adds a second, previously-missing layer: lending capacity as an external constraint discovered during live testing on 2026-10-18 (Wallex returned "ظرفیت تمام شده" for all 30 combinations tested).

Two forces must be reconciled:
1. Human intent: the user explicitly declares a regime direction (bearish/bullish/neutral) and its TTL.
2. System presence: the user must be actively watching, or the bot pauses.

## Decision

### 1. Two-layer signal model
- Layer 1 (Human): HumanSignal with explicit direction + TTL. No auto-regime detection in Phase 0.
- Layer 2 (Presence): presence tracker (48h/72h/96h) that pauses new entries or closes positions based on inactivity.

### 2. HumanSignal schema

    @dataclass(frozen=True)
    class HumanSignal:
        direction: Literal["bearish", "bullish", "neutral"]
        set_at: datetime
        expires_at: datetime
        set_by: Literal["dashboard", "endpoint", "cli", "test"]
        note: Optional[str] = None

- set_signal(direction, ttl_days, set_by, note) with validation:
  - direction in {bearish, bullish, neutral}
  - ttl_days in [1, 90]
  - set_by in {dashboard, endpoint, cli, test}
- TTL default: 10 days (locked by Hosein, 2026-10-18).


### 3. current_regime as derived property (NOT stored)
- Removed from BearHunterState as a field.
- Replaced with @property:
  - bearish -> "bear"
  - bullish -> "bull"
  - neutral -> "range"
  - None -> "idle"
- Rationale: single source of truth, no drift between signal and regime.

### 4. Phase A order + check_index
Phase A checks (0-indexed for audit clarity):
1. initialized
2. kill_switch (auto or manual)
3. paper_mode
4. human_signal_present
5. human_signal_not_expired
6. signal_bearish
7. presence (48h warning)
8. signal_freshness

- PreFlightResult.check_index: int = -1 (default -1 = not reached). Each reject sets check_index = len(passed).
- Check 6 in the older draft (current_regime != "bear") is removed — redundant with signal_bearish once current_regime became derived.
- Audit trail records check_index for post-mortem analysis.

### 5. Signal change behavior — stop new entries, do NOT close positions
- set_signal() only updates state. It does NOT touch open_positions.
- Open positions close via one of three mechanisms:
  1. Stop-loss (3%) — mandatory per config
  2. Take-profit (4.5%) — mandatory per config
  3. Max hold hours (config.max_hold_hours = 6) — closes position after N hours regardless of PnL
- Rationale: closing by signal change would cause cascading panics and lock losses at the worst moment.
- Test: test_set_signal_preserves_open_positions verifies this.

### 6. Paper mode hybrid (Week 1: MA200 auto-signal; Weeks 2-4: manual)
- Week 1: _generate_mock_signal uses MA200 cross to auto-set the paper regime.
- Weeks 2-4: user explicitly sets HumanSignal via the endpoint.
- Graduation to live requires Phase 5 checklist (see ADR 0011).


### 7. Lending capacity as external constraint -> WAITING_LIQUIDITY state
Discovery: On 2026-10-18, all 30 market/size combinations returned NO_LIQUIDITY. This is not a bug — it is Wallex's margin capacity, which can be zero for hours or days.

- New state: WAITING_LIQUIDITY (distinct from IDLE).
  - IDLE: signal is neutral or missing -> no intent to trade.
  - WAITING_LIQUIDITY: signal is bearish, all checks pass, but dry_run returned NO_LIQUIDITY.
- state.last_known_liquidity[market] = {available: bool, checked_at: iso} caches the last result (TTL 5 min).
- A background monitor (scripts/liquidity_monitor.py) polls every hour and writes to data/bots/bear_hunter/liquidity_log.jsonl.

### 8. Migration rule — legacy current_regime = "bear" -> kill switch
When from_dict() encounters a legacy state file with:
- current_regime = "bear" AND
- human_signal is None

-> The bot CANNOT know the user's actual intent. Fail-safe: kill_switch_auto = True with reason legacy_bear_without_human_signal.

For legacy current_regime in {range, bull} -> no kill switch.

## Consequences

- Positive:
  - Single source of truth for regime (derived).
  - Auditable Phase A order with check_index.
  - WAITING_LIQUIDITY distinguishes "no intent" from "intent but blocked".
  - Signal change is safe by design.
  - Migration cannot silently change user intent.

- Negative:
  - One more state to reason about (WAITING_LIQUIDITY).
  - Migration rule makes legacy bear state non-resumable without explicit set_signal.
  - datetime in HumanSignal requires careful serialization.

- Neutral:
  - check_index default -1 means old tests don't need updates.
  - Signal TTL of 10 days is generous.

## References

- ADR 0017 — Wallex View Token (auth base)
- ADR 0018 — FIFO Cost Basis
- ADR 0019 — Margin Trading & Bear Hunter Bot
- app/services/bots/bear_hunter/state.py — HumanSignal, set_signal, from_dict
- app/services/bots/bear_hunter/pre_flight.py — Phase A with check_index
- scripts/liquidity_monitor.py — background monitor
- data/bots/bear_hunter/liquidity_log.jsonl — evidence of 2026-10-18 NO_LIQUIDITY
