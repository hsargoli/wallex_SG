# 0006. Price Change Source

**Status:** Accepted
**Date:** 2026-10-08
**Deciders:** Hosein

## Context

`change_24h` was computed independently in two endpoints:

- `GET /v1/markets` → from Wallex `stats.24h_ch`
- `POST /v1/signals/batch` → from local candle arithmetic

The same symbol showed different percentages in different pages of our
own UI. SANDTMN was one example: 3.58 (markets) vs 2.86 (signals) at the
same moment. The Wallex UI showed 2.94. Three different numbers.

Root causes:

1. **Two sources of truth.** Each endpoint computed its own value.
2. **Rolling window vs candle-aligned.** Wallex computes change over
   the last 24h from "right now"; our code compared the close of the
   last candle to the close 24 candles earlier. This offsets by up to
   the candle duration (1h) and diverges in volatile markets.
3. **In-progress candle.** The last candle's close equals the current
   price, but it is not yet a settled value.

## Decision

Wallex `stats.24h_ch` and `stats.7d_ch` are the **single source of truth**
for price change across the whole platform.

Implementation details:

- `get_batch_signals` fetches `exchange.get_markets()` **once** per
  request and builds `{symbol: Market}`.
- This `market_map` is passed to every `_fetch_signal_for` task — no
  extra HTTP per symbol, no N+1 calls.
- Candle-derived computation is **fallback only**, and only when Wallex
  returns no value.

Rationale:

- **User trust.** If the user sees one number on Wallex and a different
  number in our platform, trust is lost. This is not a cosmetic issue.
- **Correctness.** Rolling window matches what the exchange reports and
  what traders expect.
- **Resilience.** Fallback keeps the feature alive if Wallex's stats are
  briefly unavailable.

## Consequences

- Signals, Markets, and Wallex UI all show the same number.
- `change_7d` becomes non-null for most symbols (was null in signals
  before because batch did not request enough candles for a 7-day
  lookback).
- One less source of divergence to maintain.
- If Wallex stats are missing for a symbol, fallback path still works
  — the UI never shows a broken state.

## References

- `app/presentation/api/v1/signals.py` — `_fetch_signal_for`, `get_batch_signals`
- `app/infrastructure/exchange/wallex/mapper.py` — `map_ticker_stats`
- `app/domain/entities/market.py` — `TickerStats.daily_change_percent`, `weekly_change_percent`
- ADR-0001 (live trading default)
