# 0001. Live Trading Default

**Status:** Accepted
**Date:** 2026-10-08
**Deciders:** Hosein

## Context

`GET /v1/orders/trading-mode` returns `{"live_enabled": true}`.
`.env.example` defaults `LIVE_TRADING_ENABLED=false`, but the local `.env`
is set to `true`. The running service can place real orders on the Wallex
exchange right now.

The original Phase 0 plan proposed forcing this to `false` until auth and
risk controls are in place.

## Decision

Do NOT change `LIVE_TRADING_ENABLED`. It stays `true` in the local environment.

Rationale (Hosein): portfolio size is small enough that the financial risk
of a bad order is acceptable. Adding auth + risk controls first would slow
down iteration.

## Consequences

- The running backend can place real orders at any time.
- No auth or rate-limiting protects the order endpoints.
- `.env.example` remains `false` — intentional, so new environments are safe.
- Revisit in Phase 2 (risk controls) and Phase 4 (real live).
- If portfolio grows, this ADR must be superseded.

## References

- `.env.example` line 25
- Endpoint: `GET /v1/orders/trading-mode`
