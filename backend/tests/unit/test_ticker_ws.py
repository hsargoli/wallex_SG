"""تست WallexTickerClient — unit، بدون اتصال واقعی به Wallex."""

from __future__ import annotations

from typing import Any

import pytest

from app.infrastructure.exchange.wallex.ticker_ws import WallexTickerClient


class FakeWS:
    """ماکت websocket — فقط send() رو ثبت می‌کنه."""

    def __init__(self) -> None:
        self.sent: list[str] = []

    def send(self, msg: str) -> None:
        self.sent.append(msg)


@pytest.fixture
def ticks() -> list[dict[str, Any]]:
    """لیست خالی که tick-های دریافتی رو جمع می‌کنه."""
    return []


@pytest.fixture
def client(ticks: list[dict[str, Any]]) -> WallexTickerClient:
    """کلاینت با callback که tick رو به لیست اضافه می‌کنه."""
    return WallexTickerClient(on_tick=ticks.append)


# ---------------------------------------------------------------------------
# _handle_message — PONG
# ---------------------------------------------------------------------------
class TestHandleMessagePong:
    def test_ping_sends_pong(self, client: WallexTickerClient) -> None:
        ws = FakeWS()
        client._handle_message(ws, "2")  # type: ignore[arg-type]
        assert ws.sent == ["3"]

    def test_pong_does_not_trigger_tick(
        self, client: WallexTickerClient, ticks: list[dict[str, Any]]
    ) -> None:
        ws = FakeWS()
        client._handle_message(ws, "2")  # type: ignore[arg-type]
        assert ticks == []


# ---------------------------------------------------------------------------
# _handle_message — Socket.IO control packets (ignore)
# ---------------------------------------------------------------------------
class TestHandleMessageControl:
    def test_connect_ack_ignored(
        self, client: WallexTickerClient, ticks: list[dict[str, Any]]
    ) -> None:
        ws = FakeWS()
        client._handle_message(ws, '40{"sid":"abc"}')  # type: ignore[arg-type]
        assert ticks == []
        assert ws.sent == []

    def test_non_array_message_ignored(
        self, client: WallexTickerClient, ticks: list[dict[str, Any]]
    ) -> None:
        ws = FakeWS()
        client._handle_message(ws, "some-text")  # type: ignore[arg-type]
        assert ticks == []


# ---------------------------------------------------------------------------
# _handle_message — ticker data
# ---------------------------------------------------------------------------
class TestHandleMessageTicker:
    def test_valid_ticker_calls_on_tick(
        self, client: WallexTickerClient, ticks: list[dict[str, Any]]
    ) -> None:
        ws = FakeWS()
        msg = '["all@price",{"symbol":"BTCTMN","price":"100","24h_ch":1.5}]'
        client._handle_message(ws, msg)  # type: ignore[arg-type]
        assert len(ticks) == 1
        assert ticks[0]["symbol"] == "BTCTMN"
        assert ticks[0]["price"] == "100"
        assert ticks[0]["24h_ch"] == 1.5

    def test_wrong_channel_ignored(
        self, client: WallexTickerClient, ticks: list[dict[str, Any]]
    ) -> None:
        ws = FakeWS()
        msg = '["other@channel",{"symbol":"BTCTMN"}]'
        client._handle_message(ws, msg)  # type: ignore[arg-type]
        assert ticks == []

    def test_bad_json_ignored(
        self, client: WallexTickerClient, ticks: list[dict[str, Any]]
    ) -> None:
        ws = FakeWS()
        client._handle_message(ws, "[not, valid, json")  # type: ignore[arg-type]
        assert ticks == []

    def test_wrong_shape_ignored(
        self, client: WallexTickerClient, ticks: list[dict[str, Any]]
    ) -> None:
        ws = FakeWS()
        # آرایه‌ی ۳ عضوی — انتظار: ignore
        client._handle_message(ws, '["all@price",{},{}]')  # type: ignore[arg-type]
        assert ticks == []

    def test_data_not_dict_ignored(
        self, client: WallexTickerClient, ticks: list[dict[str, Any]]
    ) -> None:
        ws = FakeWS()
        client._handle_message(ws, '["all@price","just-string"]')  # type: ignore[arg-type]
        assert ticks == []


# ---------------------------------------------------------------------------
# _handle_message — on_tick exception safety
# ---------------------------------------------------------------------------
class TestHandleMessageSafety:
    def test_on_tick_exception_does_not_crash(self) -> None:
        def bad_callback(data: dict[str, Any]) -> None:
            raise RuntimeError("boom")

        client = WallexTickerClient(on_tick=bad_callback)
        ws = FakeWS()
        msg = '["all@price",{"symbol":"BTCTMN","price":"1","24h_ch":0.0}]'
        # نباید raise کنه
        client._handle_message(ws, msg)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# lifecycle — start / stop
# ---------------------------------------------------------------------------
class TestLifecycle:
    def test_stop_without_start_is_safe(self) -> None:
        client = WallexTickerClient(on_tick=lambda d: None)
        client.stop()  # نباید raise کنه

    def test_start_creates_thread(self) -> None:
        client = WallexTickerClient(
            on_tick=lambda d: None,
            url="ws://invalid.local:1/ws",  # اتصال نمی‌شه، ولی thread شروع می‌شه
        )
        client.start()
        assert client._thread is not None
        assert client._thread.is_alive()
        client.stop(timeout=6.0)
        assert not client._thread.is_alive()

    def test_double_start_warns_not_new_thread(self) -> None:
        client = WallexTickerClient(
            on_tick=lambda d: None,
            url="ws://invalid.local:1/ws",
        )
        client.start()
        first_thread = client._thread
        client.start()  # باید warning بده، thread جدید نسازه
        assert client._thread is first_thread
        client.stop(timeout=6.0)
