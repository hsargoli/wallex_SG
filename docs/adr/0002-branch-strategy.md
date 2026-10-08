# 0002. Branch Strategy

**Status:** Accepted
**Date:** 2026-10-08
**Deciders:** Hosein

## Context

Current branches:

- `refactor/full-ddd` (HEAD — most active)
- `master`
- `feature-day-2026-10-05`
- `refactor/ddd-and-portability`
- `rescue-crosshair`

`master` is behind `refactor/full-ddd`. There is no clearly declared mainline.

## Decision

1. `refactor/full-ddd` is the mainline.
2. `master` fast-forwarded from it on 2026-10-08
   (109 files changed, 16455 insertions — master was far behind).
3. Old branches tagged and preserved:
   - `archive/2026-10-08/master` (pre-merge state)
   - `archive/2026-10-08/refactor-ddd-and-portability`
   - `archive/2026-10-08/rescue-crosshair`

## Consequences

- Single source of truth for the codebase.
- Old branches remain recoverable via tag.
- `git branch -a` becomes shorter.

## References

- `git branch -a` output 2026-10-08
