# 0021. Short Strategy (Human-in-the-Loop)

**Status:** Accepted
**Date:** 2026-10-18
**Deciders:** Hosein, Di (Sahara), Di (Darya)

## Context
We need a stable strategy for `bear_hunter`. Backtests showed that pure auto-regime detection (EMA 200) or fixed-indicator strategies (RSI cross) perform poorly in trending crypto markets, especially when fees are accounted for.

## Decision
We adopt a **Cooperation Strategy** (Human-in-the-Loop):
1. **Human** provides the macro direction (`bearish` / `bullish` / `neutral`).
2. **Bot** finds the micro entry point:
   - Shorts at RSI wave tops (RSI > 70 crossing down).
   - Longs at RSI wave bottoms (RSI < 30 crossing up).
3. **Bot** manages the exit:
   - Stop Loss: `1.5 * ATR` (dynamic, based on volatility).
   - Take Profit: `3.0 * ATR`.
   - Trailing Stop: `3.0 * ATR` (prevents premature exits due to noise).

## Consequences
- Bot does not guess the regime, avoiding whipsaws.
- Execution is based on real-time market data (fetched via UDF).
- Human has ultimate control.
