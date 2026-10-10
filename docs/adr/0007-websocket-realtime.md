# 0007. Real-time Prices via Wallex Socket.IO

**Status:** Accepted
**Implementation:** MVP in progress (phase 1)
**Date:** 2026-10-10
**Deciders:** Hosein, Di

## Context

The frontend currently polls via React Query with intervals from 3s to 120s.
Multiple components on the same page each poll independently. Opening 2-3
tabs multiplies the load: N clients x M components = redundant requests
against both our backend and the Wallex REST API. This creates a rate-limit
risk and lags the UI.

Discovery (2026-10-09): Wallex exposes a Socket.IO endpoint at
`wss://api.wallex.ir/ws`. A manual HTTP/1.1 Upgrade returned
`101 Switching Protocols` followed by an Engine.IO handshake
(`{"sid":...,"pingInterval":20000,"pingTimeout":30000}`).

Documented channels include `all@price` (all markets), `MARKET@trade`,
`MARKET@buyDepth`, and private channels. Connection limits: 30-minute
lifetime, server PING every 20s, max 100 PONGs per connection.

## Decision

We will build real-time price streaming for tickers. The backend will
maintain a single Socket.IO connection to Wallex and fan out updates to
our own clients.

Final architecture (A/B/C) is deferred to an Update section after
exploration in `backend/scripts/explore_wallex_ws.py`:
- A) Socket.IO end-to-end (Wallex -> backend -> frontend)
- B) Socket.IO in (Wallex -> backend), native WS out (backend -> frontend)
- C) Centralized polling + cache in backend, push to frontend

## Consequences

- Positive: removes N x M redundant requests; true push; lower Wallex load.
- Negative: 1-2 new dependencies (python-socketio backend, socket.io-client
  frontend if option A/B); backend becomes stateful (ConnectionManager).
- Neutral: polling remains as fallback; two code paths to maintain.

## Alternatives

1. Cache TTL in backend (5s). Simple, but still pull-based; no push.
2. Centralized polling in backend. Reduces load, still not real-time.
3. Do nothing. N x M problem remains.

## Risks

- **Memory leak in subscribers**: every WS client must unsubscribe on
  disconnect; a missed `finally` leaks queues silently. Mitigated by
  `test_unsubscribe_no_leak` (subscribe/unsubscribe 10x, assert empty).
- **Multi-worker (Phase 1 Postgres)**: with `uvicorn --workers N`, each
  worker opens its own Wallex connection. Mitigation (future): Redis pub/sub.
- **Wallex disconnect**: single upstream connection; if Wallex drops,
  clients are blind until reconnect. Mitigation: auto-reconnect + polling
  fallback in frontend with stale indicator.
- **nginx (Phase 5)**: requires Upgrade header passthrough config.
- **PONG cap**: max 100 PONGs (~33 min); we reconnect at 25 min.

## Future Work (post-MVP)

This MVP is not the final architecture. Known limitations:

### 1. Multi-worker support
Redis pub/sub between workers so all clients see all ticks.

### 2. Microservice migration
Extract Wallex client into a standalone Python service that writes to
Redis; FastAPI reads from Redis. Removes the thread bridge entirely.

### 3. Metrics & monitoring
- live connection count
- ticks per second
- reconnect time
- alert if Wallex silent > 30s
## Rollback

git reset --hard v0.9-pre-websocket

## References

- docs/AI_PROJECT_GUIDE.md
- docs/ROADMAP.md
- https://developers.wallex.ir/docs/socket-intro

## Update — 2026-10-10: Decision Final

Explored Wallex WS with raw `websocket-client`
(see `backend/scripts/explore_wallex_ws.py`). Confirmed working:

- URL: `wss://api.wallex.ir/ws` (no trailing slash)
- Engine.IO handshake on connect, then send `"40"` for Socket.IO
- Subscribe: `["subscribe", {"channel": "all@price"}]`
- Message format: `["all@price", {"symbol", "price", "24h_ch"}]`

**Architecture chosen: B.**

- Backend: raw `websocket-client` -> Wallex (1 connection)
- Backend: native FastAPI WebSocket -> frontend (N connections)
- Frontend: browser-native WebSocket (zero dependency)
- Message: flat `{symbol, price, 24h_ch}` (no envelope)

**Rejected:**

- A (python-socketio end-to-end): library appends trailing slash,
  incompatible with Wallex `/ws`
- C (centralized polling): still pull-based, not real-time

Status: Proposed -> Accepted
