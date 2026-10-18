# 0022. Paper Mode Infrastructure

**Status:** Accepted
**Date:** 2026-10-18
**Deciders:** Hosein, Di (Sahara), Di (Darya)

## Context
Initially, we created a `PaperAdapter` that faked balance and liquidity to allow the runner to work offline. This was a critical mistake: it hid connection issues and made the 30-day paper mode meaningless.

## Decision
1. **Remove `PaperAdapter` entirely.**
2. **Real Data:** The bot must fetch real candles and real liquidity (`dry_run`) from Wallex APIs.
3. **Fake Execution:** `PaperExecutor` only intercepts `open_position` and `close_position`, creating virtual positions.
4. **Tick Interval:** 300 seconds (5 minutes) to respect Wallex API rate limits.
5. **Mock Guard:** `_generate_mock_signal` is removed. Real `_generate_signal` is used. A strict guard prevents trading if `paper_mode=False` without a real API connection.

## Consequences
- Paper mode now tests the real infrastructure end-to-end (except real money).
- 30-day observation is meaningful.
