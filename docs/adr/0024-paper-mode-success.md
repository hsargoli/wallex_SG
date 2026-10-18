# 0024. Paper Mode Success Criteria

**Status:** Proposed
**Date:** 2026-10-18
**Deciders:** Hosein, Di (Sahara), Di (Darya)

## Context
Paper Mode is 30 days. But "success" is undefined. This ADR defines the
criteria for graduating to Live Mode.

## Decision

### 30-Day Success Criteria (ALL must be met)
| # | Metric | Threshold |
|---|--------|-----------|
| 1 | Total trades | ≥ 10 |
| 2 | Win rate | ≥ 40% |
| 3 | Net PnL | > 0% (or ≥ -2%) |
| 4 | Max drawdown | ≤ 5% |
| 5 | Kill switch auto-triggered | 0 |
| 6 | Daily loss limit hit | ≤ 1 |
| 7 | waiting_liquidity continuous | < 7 days |
| 8 | Reconcile mismatch | 0 |
| 9 | Unexpected crash/restart | 0 |

### After 30 Days
1. Bot goes IDLE automatically (no auto-live).
2. User receives alert with all metrics.
3. User decides: **Live (with real money) OR continue Paper (30 more days) OR abort**.

### Live Graduation (Phase 5)
Requires all 9 criteria +:
- ADR 0011 checklist (staged capital: 10% → 30% → 100%).
- Manual typed confirmation.

## Consequences
- No "auto-live" — user must explicitly approve.
- Metrics are auditable (stored in state.json).
- If criteria not met, bot stays in Paper Mode.

## References
- ADR 0020 (human-in-the-loop)
- ADR 0022 (paper mode infrastructure)
- ADR 0023 (capital revision)
