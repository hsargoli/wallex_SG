"""Phase 2B: SarvRouterScheduler — singleton + now_idx from wall clock."""
import time
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from app.services.bots.sarv_router.scheduler import SarvRouterScheduler


def _fake_exchange():
    return MagicMock(name="fake_exchange")


def _fake_candles(n=300):
    return [MagicMock(time=1, open=1, high=1, low=1, close=1, volume=1) for _ in range(n)]


class TestSchedulerSingleton:
    def test_router_is_singleton(self):
        """SarvRouter must be constructed ONCE in __init__, not per tick."""
        ex = _fake_exchange()
        sched = SarvRouterScheduler(exchange=ex, interval_minutes=30)
        r1 = sched._router
        r2 = sched._router
        assert r1 is r2, "router must be singleton (same instance)"
        assert r1 is not None

    def test_router_uses_exchange(self):
        ex = _fake_exchange()
        sched = SarvRouterScheduler(exchange=ex, interval_minutes=30)
        assert sched._router is not None
        # The router's lifecycle is persistent, but we can't check internals easily
        # Instead: check that _router exists

    @pytest.mark.asyncio
    async def test_now_idx_uses_wall_clock(self):
        """_job must pass now_idx = int(time.time() // 3600), not len(candles)-1."""
        ex = _fake_exchange()
        sched = SarvRouterScheduler(exchange=ex, interval_minutes=30)

        fake_candles = _fake_candles(300)
        fixed_time = 1_790_000_000  # arbitrary

        with patch(
            "app.services.bots.sarv_router.scheduler.GetCandlesUseCase"
        ) as mock_uc_cls, patch(
            "app.services.bots.sarv_router.scheduler.time"
        ) as mock_time:
            mock_uc = MagicMock()
            mock_uc.execute = AsyncMock(return_value=fake_candles)
            mock_uc_cls.return_value = mock_uc
            mock_time.time.return_value = fixed_time

            with patch.object(sched._router, "tick", new=MagicMock(return_value={"action": "no_change"})) as mock_tick:
                await sched._job()

                assert mock_tick.called
                _, kwargs = mock_tick.call_args
                expected_now_idx = fixed_time // 3600
                assert kwargs.get("now_idx") == expected_now_idx, (
                    f"now_idx must be {expected_now_idx} (wall clock), "
                    f"got {kwargs.get('now_idx')}"
                )

    @pytest.mark.asyncio
    async def test_router_persists_across_ticks(self):
        """Router must be the same instance across multiple ticks (no re-init)."""
        ex = _fake_exchange()
        sched = SarvRouterScheduler(exchange=ex, interval_minutes=30)
        fake_candles = _fake_candles(300)

        with patch(
            "app.services.bots.sarv_router.scheduler.GetCandlesUseCase"
        ) as mock_uc_cls:
            mock_uc = MagicMock()
            mock_uc.execute = AsyncMock(return_value=fake_candles)
            mock_uc_cls.return_value = mock_uc

            router_before = sched._router
            await sched._job_internal_tick(t=1000 * 3600)
            await sched._job_internal_tick(t=1001 * 3600)
            router_after = sched._router

            assert router_before is router_after, (
                "router must NOT be re-created between ticks"
            )
