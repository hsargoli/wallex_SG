"""تست TickerFanout — bridge thread ↔ asyncio، بدون اتصال واقعی."""

from __future__ import annotations

import asyncio
from typing import Any

import pytest
import pytest_asyncio

from app.presentation.api.v1.realtime import TickerFanout


@pytest_asyncio.fixture
async def fanout() -> TickerFanout:
    return TickerFanout(asyncio.get_running_loop())


# ---------------------------------------------------------------------------
# subscribe / unsubscribe
# ---------------------------------------------------------------------------
class TestSubscribe:
    async def test_subscribe_returns_queue(self, fanout: TickerFanout) -> None:
        q = fanout.subscribe("BTCTMN")
        assert isinstance(q, asyncio.Queue)
        assert fanout.subscriber_count == 1

    async def test_multiple_subscribers_same_symbol(self, fanout: TickerFanout) -> None:
        q1 = fanout.subscribe("BTCTMN")
        q2 = fanout.subscribe("BTCTMN")
        assert q1 is not q2
        assert fanout.subscriber_count == 2

    async def test_subscribe_different_symbols(self, fanout: TickerFanout) -> None:
        fanout.subscribe("BTCTMN")
        fanout.subscribe("ETHTMN")
        assert fanout.subscriber_count == 2


class TestUnsubscribe:
    async def test_unsubscribe_removes_queue(self, fanout: TickerFanout) -> None:
        q = fanout.subscribe("BTCTMN")
        fanout.unsubscribe("BTCTMN", q)
        assert fanout.subscriber_count == 0

    async def test_unsubscribe_no_leak(self, fanout: TickerFanout) -> None:
        """حیاتی: ۱۰ بار subscribe/unsubscribe → subscriber_count == 0."""
        for _ in range(10):
            q = fanout.subscribe("BTCTMN")
            fanout.unsubscribe("BTCTMN", q)
        assert fanout.subscriber_count == 0

    async def test_unsubscribe_twice_is_safe(self, fanout: TickerFanout) -> None:
        q = fanout.subscribe("BTCTMN")
        fanout.unsubscribe("BTCTMN", q)
        fanout.unsubscribe("BTCTMN", q)  # نباید raise کنه
        assert fanout.subscriber_count == 0

    async def test_unsubscribe_unknown_symbol_safe(self, fanout: TickerFanout) -> None:
        q: asyncio.Queue = asyncio.Queue()
        fanout.unsubscribe("NOPE", q)  # نباید raise کنه
        assert fanout.subscriber_count == 0


# ---------------------------------------------------------------------------
# on_tick — از thread
# ---------------------------------------------------------------------------
class TestOnTick:
    async def test_on_tick_updates_latest(self, fanout: TickerFanout) -> None:
        data = {"symbol": "BTCTMN", "price": "100"}
        fanout.on_tick(data)
        assert fanout.latest("BTCTMN") == data

    async def test_on_tick_ignores_missing_symbol(self, fanout: TickerFanout) -> None:
        fanout.on_tick({"price": "100"})  # بدون symbol
        assert fanout.latest("BTCTMN") is None

    async def test_on_tick_ignores_non_string_symbol(self, fanout: TickerFanout) -> None:
        fanout.on_tick({"symbol": 123, "price": "100"})
        assert fanout.subscriber_count == 0

    async def test_latest_unknown_symbol_is_none(self, fanout: TickerFanout) -> None:
        assert fanout.latest("NOPE") is None


class TestOnTickPush:
    async def test_on_tick_pushes_to_subscriber(self, fanout: TickerFanout) -> None:
        q = fanout.subscribe("BTCTMN")
        data = {"symbol": "BTCTMN", "price": "100"}
        fanout.on_tick(data)
        await asyncio.sleep(0.05)  # let call_soon_threadsafe run
        assert q.qsize() == 1
        got = await q.get()
        assert got == data

    async def test_on_tick_no_subscribers_no_error(self, fanout: TickerFanout) -> None:
        fanout.on_tick({"symbol": "BTCTMN", "price": "100"})
        await asyncio.sleep(0.05)
        # فقط latest آپدیت شده، بدون crash
        assert fanout.latest("BTCTMN") is not None

    async def test_on_tick_only_matching_symbol(self, fanout: TickerFanout) -> None:
        q = fanout.subscribe("BTCTMN")
        fanout.on_tick({"symbol": "ETHTMN", "price": "5"})
        await asyncio.sleep(0.05)
        assert q.qsize() == 0  # ETHTMN نباید به BTCTMN برسه

    async def test_queue_full_drops_oldest(self, fanout: TickerFanout) -> None:
        """queue پر شد → قدیمی‌ها drop، جدیدها می‌مونن."""
        q = fanout.subscribe("BTCTMN")
        for i in range(120):  # بیشتر از maxsize=100
            fanout.on_tick({"symbol": "BTCTMN", "price": str(i)})
        await asyncio.sleep(0.1)
        assert q.qsize() <= 100  # هرگز بیشتر از maxsize
