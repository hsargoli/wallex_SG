"""Real-time WebSocket — /ws/ticker/{symbol}.

زنجیره: Wallex (Socket.IO) → WallexTickerClient (thread) → TickerFanout → endpoint
"""

from __future__ import annotations

import asyncio
from typing import Any

import structlog
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter(tags=["realtime"])
log = structlog.get_logger("api.realtime")

QUEUE_MAXSIZE = 100


class TickerFanout:
    """Bridge thread ↔ asyncio. توزیع ticker بین کلاینت‌ها.

    on_tick از thread صدا زده می‌شه (call_soon_threadsafe).
    subscribe/unsubscribe از event loop.
    """

    def __init__(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop
        self._latest: dict[str, dict[str, Any]] = {}
        self._subscribers: dict[str, set[asyncio.Queue]] = {}

    # ----- از thread -----
    def on_tick(self, data: dict[str, Any]) -> None:
        symbol = data.get("symbol")
        if not isinstance(symbol, str):
            return
        self._latest[symbol] = data
        queues = self._subscribers.get(symbol)
        if not queues:
            return
        targets = list(queues)
        self._loop.call_soon_threadsafe(self._push, targets, data)

    def _push(self, queues: list[asyncio.Queue], data: dict[str, Any]) -> None:
        """تو event loop — drop oldest اگر پر شد (قیمت تازه مهم‌تره)."""
        for q in queues:
            try:
                q.put_nowait(data)
            except asyncio.QueueFull:
                try:
                    q.get_nowait()
                    q.put_nowait(data)
                except (asyncio.QueueEmpty, asyncio.QueueFull):
                    pass

    # ----- از event loop -----
    def latest(self, symbol: str) -> dict[str, Any] | None:
        return self._latest.get(symbol)

    def subscribe(self, symbol: str) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue(maxsize=QUEUE_MAXSIZE)
        self._subscribers.setdefault(symbol, set()).add(q)
        return q

    def unsubscribe(self, symbol: str, q: asyncio.Queue) -> None:
        queues = self._subscribers.get(symbol)
        if not queues:
            return
        queues.discard(q)
        if not queues:
            del self._subscribers[symbol]

    @property
    def subscriber_count(self) -> int:
        """برای تست no-leak."""
        return sum(len(s) for s in self._subscribers.values())


@router.websocket("/ws/ticker/{symbol}")
async def ticker_ws(websocket: WebSocket, symbol: str) -> None:
    await websocket.accept()
    symbol = symbol.upper()
    fanout: TickerFanout = websocket.app.state.ticker_fanout

    latest = fanout.latest(symbol)
    if latest is not None:
        await websocket.send_json(latest)

    queue = fanout.subscribe(symbol)
    log.info("ws.subscribed", symbol=symbol)
    try:
        while True:
            data = await queue.get()
            await websocket.send_json(data)
    except WebSocketDisconnect:
        log.info("ws.disconnected", symbol=symbol)
    finally:
        fanout.unsubscribe(symbol, queue)
        log.info("ws.unsubscribed", symbol=symbol)
