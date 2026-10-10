"""WallexTickerClient — اتصال sync به Wallex Socket.IO در thread جدا.

معماری:
  - thread daemon که به wss://api.wallex.ir/ws وصل می‌شه
  - هر tick → on_tick callback (از thread صدا زده می‌شه)
  - PONG خودکار (پاسخ "3" به "2" سرور)
  - reconnect قبل از ۲۵ دقیقه (سقف Wallex: ۳۰ دقیقه)

هشدار: on_tick از thread صدا زده می‌شه. اگر async لازم داری،
        خودت call_soon_threadsafe رو صدا بزن.
"""

from __future__ import annotations

import json
import threading
import time
from collections.abc import Callable
from typing import Any

import structlog
import websocket

WALLEX_WS_URL = "wss://api.wallex.ir/ws"
SUBSCRIBE_CHANNEL = "all@price"
RECONNECT_BEFORE_SECONDS = 25 * 60  # 25 min (Wallex limit: 30 min)
RECONNECT_WAIT_SECONDS = 5.0


class WallexTickerClient:
    """کلاینت ticker والکس — sync، در thread جدا.

    استفاده:
        client = WallexTickerClient(on_tick=lambda d: print(d))
        client.start()
        ...
        client.stop()
    """

    def __init__(
        self,
        on_tick: Callable[[dict[str, Any]], None],
        url: str = WALLEX_WS_URL,
        reconnect_before: int = RECONNECT_BEFORE_SECONDS,
    ) -> None:
        """on_tick: callback که هر tick (dict) رو دریافت می‌کنه."""
        self._on_tick = on_tick
        self._url = url
        self._reconnect_before = reconnect_before
        self._log = structlog.get_logger("wallex.ticker_ws")
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        """شروع thread پس‌زمینه."""
        if self._thread is not None and self._thread.is_alive():
            self._log.warning("ticker_ws.already_running")
            return
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run,
            name="wallex-ticker",
            daemon=True,
        )
        self._thread.start()
        self._log.info("ticker_ws.started", url=self._url)

    def stop(self, timeout: float = 5.0) -> None:
        """توقف تمیز با join روی thread."""
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=timeout)
            if self._thread.is_alive():
                self._log.warning("ticker_ws.stop_timeout")
        self._log.info("ticker_ws.stopped")

    # ------------------------------------------------------------------
    # داخلی — thread
    # ------------------------------------------------------------------
    def _run(self) -> None:
        """loop اصلی — reconnect خودکار تا stop_event."""
        while not self._stop_event.is_set():
            try:
                self._connect_and_listen()
            except Exception as exc:
                self._log.error(
                    "ticker_ws.connection_error", error=str(exc)
                )
                if self._stop_event.wait(timeout=RECONNECT_WAIT_SECONDS):
                    break
        self._log.info("ticker_ws.loop_exit")

    def _connect_and_listen(self) -> None:
        """یه اتصال — تا stop یا رسیدن به زمان reconnect."""
        ws = websocket.create_connection(self._url, timeout=3)
        try:
            # ۱. Engine.IO handshake (سرور یه open packet می‌فرسته)
            first = ws.recv()
            self._log.info("ticker_ws.handshake", data=str(first)[:120])

            # ۲. Socket.IO connect (پکت 40 = connect به namespace پیش‌فرض)
            ws.send("40")

            # ۳. subscribe به کانال
            sub = json.dumps(["subscribe", {"channel": SUBSCRIBE_CHANNEL}])
            ws.send(sub)
            self._log.info("ticker_ws.subscribed", channel=SUBSCRIBE_CHANNEL)

            # ۴. loop دریافت
            started = time.monotonic()
            while not self._stop_event.is_set():
                if time.monotonic() - started > self._reconnect_before:
                    self._log.info("ticker_ws.reconnect_scheduled")
                    break
                try:
                    msg = ws.recv()
                except websocket.WebSocketTimeoutException:
                    continue
                self._handle_message(ws, msg)
        finally:
            ws.close()

    def _handle_message(self, ws: websocket.WebSocket, msg: str) -> None:
        """PONG + parse ticker."""
        # Engine.IO ping → pong
        if msg == "2":
            ws.send("3")
            return

        # Socket.IO connect ack (40{sid:...})
        if msg.startswith("40"):
            return

        # فقط آرایه‌ها (پیام‌های data)
        if not msg.startswith("["):
            return

        try:
            parsed = json.loads(msg)
        except json.JSONDecodeError:
            self._log.warning("ticker_ws.bad_json", msg=msg[:100])
            return

        if not (isinstance(parsed, list) and len(parsed) == 2):
            return
        channel, data = parsed
        if channel != SUBSCRIBE_CHANNEL or not isinstance(data, dict):
            return

        try:
            self._on_tick(data)
        except Exception as exc:
            self._log.error("ticker_ws.on_tick_error", error=str(exc))
