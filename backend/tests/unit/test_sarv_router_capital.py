"""Phase 1B: CapitalAllocator — allocation rules per regime."""
import pytest
from app.services.bots.sarv_router.config import SarvRouterConfig
from app.services.bots.sarv_router.regime import Regime
from app.services.bots.sarv_router.capital_allocator import allocate_capital


TOTAL = 1_000_000.0


class TestCapitalAllocator:
    def test_uptrend_gives_60_to_nooaah(self):
        r = allocate_capital(TOTAL, Regime.UPTREND, SarvRouterConfig())
        assert r["regime"] == "uptrend"
        assert r["active_bots"] == ["nooaah"]
        assert r["allocations"]["nooaah"] == 600_000.0
        assert r["cash"] == 400_000.0  # 60% to bot, 40% cash (10% reserve + 30% idle)
        # Invariant: allocations + cash == total
        assert sum(r["allocations"].values()) + r["cash"] == TOTAL

    def test_range_gives_30_to_sarvban(self):
        r = allocate_capital(TOTAL, Regime.RANGE, SarvRouterConfig())
        assert r["active_bots"] == ["sarvban"]
        assert r["allocations"]["sarvban"] == 300_000.0
        assert r["cash"] == 700_000.0
        assert sum(r["allocations"].values()) + r["cash"] == TOTAL

    def test_downtrend_all_cash(self):
        r = allocate_capital(TOTAL, Regime.DOWNTREND, SarvRouterConfig())
        assert r["active_bots"] == []
        assert r["allocations"] == {}
        assert r["cash"] == TOTAL

    def test_unknown_all_cash(self):
        r = allocate_capital(TOTAL, Regime.UNKNOWN, SarvRouterConfig())
        assert r["active_bots"] == []
        assert r["allocations"] == {}
        assert r["cash"] == TOTAL

    def test_cash_reserve_always_met(self):
        """In any regime, cash >= cash_reserve_pct% of total."""
        cfg = SarvRouterConfig()
        reserve = TOTAL * cfg.cash_reserve_pct / 100.0
        for regime in (Regime.UPTREND, Regime.RANGE, Regime.DOWNTREND, Regime.UNKNOWN):
            r = allocate_capital(TOTAL, regime, cfg)
            assert r["cash"] >= reserve, f"{regime}: cash={r['cash']} < reserve={reserve}"

    def test_max_per_bot_enforced(self):
        """If regime_pct > max_per_bot_pct, allocation is capped."""
        cfg = SarvRouterConfig(uptrend_capital_pct=80.0, max_per_bot_pct=60.0)
        r = allocate_capital(TOTAL, Regime.UPTREND, cfg)
        assert r["allocations"]["nooaah"] == 600_000.0  # capped at max
        assert r["cash"] == 400_000.0

    def test_negative_total_raises(self):
        with pytest.raises(ValueError):
            allocate_capital(-100.0, Regime.UPTREND, SarvRouterConfig())

    def test_zero_total_ok(self):
        r = allocate_capital(0.0, Regime.UPTREND, SarvRouterConfig())
        assert r["allocations"]["nooaah"] == 0.0
        assert r["cash"] == 0.0
