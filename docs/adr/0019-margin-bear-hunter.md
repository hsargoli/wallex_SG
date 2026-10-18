# 0019. Margin Trading & Bear Hunter Bot

**Status:** Proposed
**Date:** 2026-10-18
**Deciders:** Hosein, Di (Live Bot)

## Context

The Live Bot mission (HANDOFF-LIVE-BOT-2026-10-18) initially assumed Wallex only supports spot trading (long-only). Therefore, the strategy for a bear market was limited to "cash is a position" (sitting out).

However, a critical discovery on 2026-10-18 confirmed that Wallex **does** provide a Margin Trading API (`margin-trade/v1/...`). The UI supports "معامله تعهدی" (Margin Trading) with leverage (up to 10x) and both Long/Short positions.

This changes the landscape: We can now build a true `bear_hunter` bot to profit in downtrends.

## Decision

We will implement Margin Trading support and a new `bear_hunter` bot.

### 1. Architecture: `MarginAdapter`
- We will NOT mix margin endpoints into the existing `WallexExchange` (spot).
- We will create a dedicated `WallexMarginAdapter` in `app/infrastructure/exchange/wallex/margin.py`.
- It will implement the required endpoints:
  - `POST /margin-trade/v1/positions` (open short/long)
  - `GET /margin-trade/v1/positions` (list open positions)
  - `POST /margin-trade/v1/public/dry-run` (simulate before opening)
  - `DELETE /margin-trade/v1/positions` (close position - assumed based on standard API patterns)

### 2. Safety Rails (Locked Decisions)
The 12 decisions from the Captain Di letter are locked. For Margin specifically, these adapt as follows:
- **Capital:** 100k TMN (initial).
- **Daily Limit:** 300k TMN.
- **Per Order Limit:** 100k TMN.
- **Max Positions:** 4.
- **Pair:** BTCTMN only.
- **Timeframe:** 1h.
- **Leverage (risk_coef):** **2x** (Strictly capped. No 10x).
- **Stop-Loss:** 3% (Mandatory).
- **Take-Profit:** 3%.
- **Cooldown:** 60 seconds.
- **8h Loss Limit:** -5% -> auto-pause.
- **Notifications:** Dashboard only.

### 3. `bear_hunter` Logic (MVP)
- **Entry:** Trigger a short position if the trend is bearish (e.g., EMA cross down, or Nooaah regime = "bear").
- **Exit:** Take profit at 3%, Stop loss at 3%, or if the market regime changes to "bull".
- **Funding Rate Awareness:** The bot must account for the 4-hour funding fee deduction. Holding a position for a long time burns collateral. The bot will favor short-term swings.

### 4. Two Non-Negotiables for Margin
1. **No order without SL/TP.** The API accepts SL/TP, the bot must send them.
2. **Liquidation Buffer.** The bot must monitor `call_price` (warning) and `liquidity_price` (liquidation). If `current_price` approaches `call_price`, it must notify the user and attempt to close or add collateral.

## Consequences

- **Positive:**
  - True hedging and profit in bear markets.
  - The platform becomes a full trading bot (Spot + Margin).
  - RegimeRouter (Phase 2) can now map "bear" to `bear_hunter` instead of "cash".
- **Negative:**
  - High complexity: Leverage = risk of total loss (liquidation).
  - API is new to us; requires careful dry-run testing.
  - Funding fees eat into profits.
- **Neutral:**
  - Requires a new DB column or table for Margin position tracking (since it differs from Spot).

## Implementation Phases

1. **Phase 1: Margin Adapter (Dry-Run Only)** -> No real orders.
2. **Phase 2: Bear Hunter Bot (Paper/Dry-run)** -> Logic and safety rails.
3. **Phase 3: Live with 100k** -> Real money, 2x leverage.

## References

- HANDOFF-LIVE-BOT-2026-10-18.md (Captain Di's letter)
- Wallex API Docs: `margin-trade/v1`
- ADR 0001 (Live Trading Default)
