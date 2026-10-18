# 0023. Capital Revision (Supersedes Locked Decision #1)

**Status:** Proposed
**Date:** 2026-10-18
**Deciders:** Hosein (pending)

## Context
Original 12 locked decisions set initial capital = 100,000 TMN.
During live testing (2026-10-18), we discovered Wallex enforces a **minimum
collateral of 3,000,000 TMN** for margin-trade positions.

With 100,000 TMN, `POST /margin-trade/v1/positions` returns 422:
"وثیقه باید بین ۳,۰۰۰,۰۰۰ و ۱۰۰,۰۰۰,۰۰۰ باشد."

This means: **100,000 TMN makes live trading impossible on Wallex margin.**

## Decision
Revise capital to **5,000,000 TMN** (above the 3M minimum, with 2M buffer).

Adjust related limits proportionally:
- `daily_volume_limit_tmn`: 300,000 → 15,000,000
- `per_order_limit_tmn`: 100,000 → 1,500,000
- `max_trades_per_day`: 3 (unchanged)
- `cooldown_seconds`: 60 (unchanged)

## Rationale
- We cannot trade below 3M. 5M is the smallest safe value with margin.
- Proportional adjustment maintains the same risk profile (5% per trade).
- Paper Mode uses 5M virtual capital; Live Mode (future) uses real 5M.

## Consequences
- Positive: Bot can actually trade on Wallex.
- Negative: Initial capital is 50x larger; if risk is not controlled, losses scale.
- Mitigation: SL/TP still 3%/4.5%, daily loss limit still 5%.

## References
- ADR 0019 (margin trading)
- ADR 0020 (human-in-the-loop)
- Wallex error: 422 "min collateral 3M"
