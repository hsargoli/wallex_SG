"""Phase 2A: SarvRouterScheduler — exchange-based data source."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.bots.sarv_router.scheduler import SarvRouterScheduler


def _fake_exchange():
    return MagicMock(name="fake_exchange")


class TestSarvRouterScheduler:
    def test_init_accepts_exchange(self):
        ex = _fake_exchange()
        sched = SarvRouterScheduler(exchange=ex, interval_minutes=30)
        assert sched._exchange is ex

    def test_init_rejects_missing_exchange(self):
        """exchange is required (no CSV fallback)."""
        with pytest.raises(TypeError):
            SarvRouterScheduler(interval_minutes=30)  # missing exchange

    @pytest.mark.asyncio
    async def test_job_fetches_from_exchange(self):
        """_job must use GetCandlesUseCase, not CSV."""
        ex = _fake_exchange()
        sched = SarvRouterScheduler(exchange=ex, interval_minutes=30)

        fake_candles = [MagicMock()] * 100
        with patch(
            "app.services.bots.sarv_router.scheduler.GetCandlesUseCase"
        ) as mock_uc_cls:
            mock_uc = MagicMock()
            mock_uc.execute = AsyncMock(return_value=fake_candles)
            mock_uc_cls.return_value = mock_uc

            with patch(
                "app.services.bots.sarv_router.scheduler.SarvRouter"
            ) as mock_sarv_cls:
                mock_sarv = MagicMock()
                mock_sarv.tick = MagicMock(return_value={"action": "no_change", "regime": "range"})
                mock_sarv_cls.return_value = mock_sarv

                await sched._job()

                # Verify GetCandlesUseCase was called with exchange
                mock_uc_cls.assert_called_once_with(exchange=ex)
                mock_uc.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_job_handles_no_candles(self):
        """_job must not crash if no candles."""
        ex = _fake_exchange()
        sched = SarvRouterScheduler(exchange=ex, interval_minutes=30)

        with patch(
            "app.services.bots.sarv_router.scheduler.GetCandlesUseCase"
        ) as mock_uc_cls:
            mock_uc = MagicMock()
            mock_uc.execute = AsyncMock(return_value=[])
            mock_uc_cls.return_value = mock_uc

            await sched._job()  # must not raise

            assert sched._last_error == "no candles loaded"
