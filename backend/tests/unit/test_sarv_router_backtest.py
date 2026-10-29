"""Phase 1G: SarvRouter backtest adapter — full simulation over candles."""
import uuid
from decimal import Decimal
import pytest
from app.domain.entities.candle import Candle
from app.services.bots.sarv_router.audit import AuditTrail
from app.services.bots.sarv_router.backtest_adapter import run_sarv_backtest
from app.services.bots.sarv_router.bot import SarvRouter
from app.services.bots.sarv_router.config import SarvRouterConfig
from app.services.bots.sarv_router.store import SarvStore


def _c(t, price):
    p = Decimal(str(price))
    return Candle(time=t, open=p, high=p+1, low=p-1, close=p, volume=Decimal("100"))


def _uptrend(n=250):
    return [_c(i*3600, 100 + i*2) for i in range(n)]


def _downtrend(n=250):
    # 250 candles from 400 down to ~50 — strong downtrend, no negative prices
    return [_c(i*3600, 400 - i*1.4) for i in range(n)]


def _mixed():
    # 100 flat, 100 up, 100 down
    out = [_c(i*3600, 100 + (i % 2)) for i in range(100)]
    for i in range(100, 200):
        out.append(_c(i*3600, 100 + (i-100)*3))
    for i in range(200, 300):
        out.append(_c(i*3600, 400 - (i-200)*3))
    return out


def _mk(tmp_path):
    calls = {"start": [], "stop": [], "stop_all": 0}
    def _start(slug): calls["start"].append(slug)
    def _stop(slug): calls["stop"].append(slug)
    def _stop_all(): calls["stop_all"] += 1
    store = SarvStore(base_dir=tmp_path)
    audit = AuditTrail(base_dir=tmp_path)
    router = SarvRouter(
        config=SarvRouterConfig(),
        start_bot=_start, stop_bot=_stop, stop_all=_stop_all,
        store=store, audit=audit,
    )
    return router, calls


class TestBacktestAdapter:
    def test_uptrend_final_state(self, tmp_path):
        router, calls = _mk(tmp_path)
        uid = str(uuid.uuid4())
        result = run_sarv_backtest(router, uid, _uptrend(250))
        assert result["total_ticks"] == 250
        assert result["final_regime"] == "uptrend"
        assert result["final_active_bots"] == ["nooaah"]
        assert result["switches"] >= 1

    def test_downtrend_no_switch_to_bot(self, tmp_path):
        router, calls = _mk(tmp_path)
        uid = str(uuid.uuid4())
        result = run_sarv_backtest(router, uid, _downtrend(250))
        assert result["final_active_bots"] == []
        assert result["final_regime"] == "downtrend"
        # Only stop_all calls, no bot starts
        assert calls["start"] == []

    def test_mixed_regime_switches(self, tmp_path):
        router, calls = _mk(tmp_path)
        uid = str(uuid.uuid4())
        result = run_sarv_backtest(router, uid, _mixed())
        assert result["switches"] >= 1
        assert len(set(result["regime_sequence"])) > 1

    def test_insufficient_candles(self, tmp_path):
        router, calls = _mk(tmp_path)
        uid = str(uuid.uuid4())
        result = run_sarv_backtest(router, uid, _uptrend(20))
        assert result["final_regime"] == "unknown"
        assert calls["start"] == []

    def test_cash_tracking_monotone(self, tmp_path):
        router, calls = _mk(tmp_path)
        uid = str(uuid.uuid4())
        result = run_sarv_backtest(router, uid, _mixed())
        # Every tick cash >= 0 and <= total
        for cash in result["cash_trace"]:
            assert 0 <= cash <= 1_000_000.0
