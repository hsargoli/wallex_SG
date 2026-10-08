# 0004. Heredoc Policy

**Status:** Accepted
**Date:** 2026-10-08
**Deciders:** Hosein

## Context

`AI_PRIMER.md` (rule 2) allows heredoc with a unique delimiter.
`docs/CONVENTIONS.md` (rule 3) forbids heredoc in the terminal for markdown.

These contradict each other.

## Decision

Heredoc is allowed when the delimiter is unique and single-quoted.

Rules:

- Delimiter MUST be unique per file (e.g. `ADR_README_EOF`, not `EOF`).
- Delimiter MUST be single-quoted: `<< 'DELIM'`.
- Bare `<< EOF` is forbidden.

`docs/CONVENTIONS.md` rule 3 is updated accordingly.

## Consequences

- `AI_PRIMER.md` rule 2 wins.
- Single source of truth for the heredoc policy.
- No more contradiction between documents.

## References

- `AI_PRIMER.md` rule 2, rule 37, rule 68
- `docs/CONVENTIONS.md` rule 3
