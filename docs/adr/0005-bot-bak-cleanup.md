# 0005. Bot .bak File Cleanup

**Status:** Proposed
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

1. First: `diff` each `.bak` against its current version to confirm no
   lost work.
2. Then: remove them in a single chore commit:
   `chore(bots): remove 12 .bak files`
3. If any `.bak` contains unique work, extract it before removal.

Final action pending witness (the diffs) and Hosein's confirmation.

## Consequences

- Cleaner tree.
- Removed history is recoverable from git only if files were ever tracked
  (they are not). So the diffs matter.

## References

- `find backend/app/services/bots -name "*.bak*"`
