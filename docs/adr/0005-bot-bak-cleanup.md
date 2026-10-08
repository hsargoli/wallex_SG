# 0005. Bot .bak File Cleanup

**Status:** Accepted
**Date:** 2026-10-08
**Deciders:** Hosein

## Context

Twelve `.bak` files exist under `backend/app/services/bots/`:

- `scalp_master/`: 7 files (bot.py.bak2-4, config.py.bak2-4, strategy.py.bak)
- `bots/`: 2 files (__init__.py.bak, __init__.py.bak2)
- `volatility_hunter/`: 1 file (config.py.bak)
- `market_scanner/`: 2 files (bot.py.bak, config.py.bak)

They are not tracked intentionally, but clutter the tree.

## Decision (proposed)

Completed 2026-10-08:

1. `diff` each `.bak` against current version — done.
2. 7 files verified as strict subsets of current → safely removable.
3. 5 files contained unique lines (12–21 each) → archived, not deleted.
4. All 12 moved from `backend/app/services/bots/` to
   `_archive/bots-bak-2026-10-08/` (gitignored, local backup only).

## Consequences

- Cleaner tree.
- Removed history is recoverable from git only if files were ever tracked
  (they are not). So the diffs matter.

## References

- `find backend/app/services/bots -name "*.bak*"`
