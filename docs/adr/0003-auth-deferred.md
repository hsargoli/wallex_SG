# 0003. Authentication Deferred to Last Phase

**Status:** Accepted
**Date:** 2026-10-08
**Deciders:** Hosein

## Context

The original plan placed authentication (JWT or session) and roles
(admin/viewer) in Phase 1, right after Phase 0.

The project is currently developed by a single person (Hosein).

## Decision

Authentication is deferred to the final phase (Phase 5).

## Consequences

- Order endpoints remain unprotected until Phase 5.
- Acceptable only because ADR-0001 accepts the live-trading risk and
  the deployment remains local / non-public.
- When the team grows or the service is exposed publicly, Phase 5
  becomes blocking.

## References

- ADR-0001
- `docs/ROADMAP.md`
