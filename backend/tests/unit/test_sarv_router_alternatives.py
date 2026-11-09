"""Phase 5 MVP: Alternatives tests (ADR-0044)."""
import pytest
from decimal import Decimal
from app.domain.entities.candle import Candle
from app.services.bots.sarv_router.regime import Regime
from app.services.bots.sarv_router.config import SarvRouterConfig
from app.services.bots.sarv_router.alternatives import get_adjacent_regimes, generate_alternatives
from app.services.bots.sarv_router.bot import SarvRouter
from app.services.bots.sarv_router.store import SarvStore
from app.services.bots.sarv_router.audit import AuditTrail


class TestAlternatives:
    def test_adjacent_uptrend(self):
        assert get_adjacent_regimes(Regime.UPTREND) == [Regime.RANGE]

    def test_adjacent_range(self):
        assert set(get_adjacent_regimes(Regime.RANGE)) == {Regime.UPTREND, Regime.DOWNTREND}

    def test_generate_alternatives(self):
        cfg = SarvRouterConfig()
        alts = generate_alternatives(Regime.UPTREND, 1_000_000.0, cfg)
        assert len(alts) == 1
        assert alts[0]["regime"] == "range"
        assert "sarvban" in alts[0]["active_bots"]

    def test_tick_includes_alternatives(self, tmp_path):
        def _c(t, price):
            p = Decimal(str(price))
            return Candle(time=t, open=p, high=p+1, low=p-1, close=p, volume=Decimal("100"))
        def _uptrend(n=300):
            return [_c(i*3600, 100 + i*2) for i in range(n)]

        router = SarvRouter(
            config=SarvRouterConfig(),
            start_bot=lambda s: None, stop_bot=lambda s: None, stop_all=lambda: None,
            store=SarvStore(base_dir=tmp_path), audit=AuditTrail(base_dir=tmp_path),
        )
        r = router.tick("u-alt", _uptrend(300), now_idx=0)
        assert "alternatives" in r
        assert len(r["alternatives"]) == 1
        assert r["alternatives"][0]["regime"] == "range"
        assert "risk" in r["alternatives"][0]
