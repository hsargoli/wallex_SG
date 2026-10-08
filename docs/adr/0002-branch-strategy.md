# 0002. Branch Strategy

**Status:** Proposed
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

## Decision (proposed)

1. `refactor/full-ddd` becomes the mainline.
2. `master` is fast-forwarded from it (or replaced by it).
3. Old branches are tagged `archive/2026-10-08` and left in place
   (not deleted — safer and reversible).

Final confirmation pending from Hosein.

## Consequences

- Single source of truth for the codebase.
- Old branches remain recoverable via tag.
- `git branch -a` becomes shorter.

## References

- `git branch -a` output 2026-10-08
