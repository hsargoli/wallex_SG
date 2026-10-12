# 0010. Live Trading Architecture

**Status:** Proposed
**Date:** 2026-10-12
**Deciders:** Hosein, Di

## Context

Nooaah v1 is validated: rule_based classifier, conf=85, cc=2, tp=3×ATR,
sl=1.5×ATR, vol_z_min=-0.5. Backtests show +27.65% in bull, 0% in bear,
-4.19% in ranging.

Now moving to live trading (real money on Wallex). Per ADR-0001,
`LIVE_TRADING_ENABLED=true` in local env, so the backend can already
place real orders via `presentation/api/v1/orders.py`.

Before going live, we need infrastructure for safe operation:
- Paper engine (dry-run before real money) — NEW
- Capital allocation (per-bot wallet)
- Automatic scheduler (bot runs independently)
- Daily loss limit (user decides, bot suggests)
- Kill-switch (emergency stop)
- Position management (max concurrent positions)

## Decision

**0. Paper engine — mandatory pre-live step.**

Before switching to real money, the bot runs in "paper" mode for at
least 24 hours: orders are simulated, not sent to Wallex. Balances
and positions are tracked in a virtual portfolio.

Activation:
- User sets `mode: paper | live` per bot in config/UI
- Default for a new bot: `paper`
- Switching to `live` requires: paper ran for ≥24h AND user confirms
  in UI ("I understand this uses real money")

Paper state:
- `data/nooaah/paper_state.json` — virtual positions, balance, trades
- Same NooaahBot logic, different execution adapter (`PaperExecutor`
  vs `LiveExecutor`)

**1. Capital allocation — user-controlled, per-bot.**

User allocates a budget from their wallet to each bot. No automatic
percentage. UI: input field with wallet balance shown.

Example:
    Wallet: 100,000,000 TMN
    → Nooaah: 5,000,000 TMN (user chooses)

**2. Max concurrent positions — per-bot config, default 1.**

Each bot has its own `max_concurrent_positions` param. For Nooaah,
default is 1 (empirically validated: max=2,3 performed worse — see
docs/nooaah_ideas.md B2). Other bots may differ; each needs its own
backtest.

UI: configurable, with recommended default.

**3. Daily loss limit — bot suggests, user decides.**

Bot calculates a recommended value based on the bot's backtest
(e.g., 2×max_dd_pct). User sees recommendation and can override.

Example:
    Nooaah backtest max DD: 4.19%
    → Recommended daily limit: 2.0%
    User: [2.0%] ← editable input

Behavior on hit:
    - Auto-stop: no new positions opened for the rest of the day
    - Alert: user notified (UI notification + log)
    - Override: user can manually resume (with explicit confirmation)

**4. Kill-switch — global emergency stop.**

Endpoint: `POST /v1/nooaah/kill`
Effect:
    - All open positions closed (market sell)
    - No new orders accepted
    - State persists (killed until `/resume`)

UI: red button at top of `/nooaah` page.

**5. Scheduler — in-process, every 1 hour.**

FastAPI lifespan starts an APScheduler job that runs `NooaahBot.run_once()`
every hour. The bot operates independently; user monitors via UI.

Not using external cron: keeps state in-process, simpler for MVP.

## Consequences

- **Positive:**
  - User has full control (capital, daily limit)
  - Multiple layers of protection (max positions, daily loss, kill-switch)
  - Bot runs independently (real "bot" behavior)
  
- **Negative:**
  - New dependency: `apscheduler`
  - Scheduler must handle errors gracefully (bot failure ≠ server crash)
  - In-process scheduler = single-worker only (Redis pub/sub needed for multi-worker — future)

- **Neutral:**
  - All config stored in state (JSON initially, DB in Phase 1)
  - Trading logs must be persistent for audit

## Alternatives Considered

**Capital allocation — automatic (fixed %):**
Rejected. User control is more transparent and matches existing
`bot-wallet` pattern in the project.

**Daily loss limit — hard-coded:**
Rejected. Market conditions vary; user should decide risk tolerance.

**Scheduler — external cron:**
Rejected for MVP. Adds infra complexity; in-process is enough for
single-worker. Revisit if scaling.

## Risks

- **Bot crash loops:** if `run_once()` throws every hour, we get log spam.
  Mitigation: catch exceptions, log, backoff on repeated failures.

- **Scheduler race with kill-switch:** if user hits kill-switch while
  bot is mid-cycle. Mitigation: kill-switch sets a flag checked at
  start of each cycle; cycle finishes current position management.

- **Wallet/position drift:** state vs Wallex actual balance could diverge.
  Mitigation: reconcile on each cycle (fetch real balance, log drift).

- **Rate limit on Wallex:** hourly = 24 req/day/bot. Low risk.

- **Single-worker only:** if uvicorn runs --workers > 1, each worker
  starts its own scheduler → duplicate orders. Mitigation: enforce
  workers=1 via deployment docs; revisit for multi-worker (Redis lock).

## Future Work

- Telegram/Email alerts on trade events
- State in Postgres (Phase 1)
- Multi-worker support via Redis pub/sub
- Per-bot backtests for max_concurrent_positions (each bot tuned)

## References

- ADR-0001 — Live Trading Default
- ADR-0008 — Nooaah Analysis DDD
- docs/nooaah_ideas.md — 18 tested ideas
- docs/reports/2026-10-11_Nooaah_UI.md
- presentation/api/v1/orders.py — existing live order endpoint
