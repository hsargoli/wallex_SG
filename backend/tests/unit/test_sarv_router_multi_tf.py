"""Phase 1J: multi-timeframe regime (1h + 4h confirmation)."""
from decimal import Decimal
from app.domain.entities.candle import Candle
from app.services.bots.sarv_router.config import SarvRouterConfig
from app.services.bots.sarv_router.regime import Regime, detect_regime_multi_tf
from app.services.bots.sarv_router.resample import resample_4h


def _c(t, price):
    p = Decimal(str(price))
    return Candle(time=t, open=p, high=p+1, low=p-1, close=p, volume=Decimal("100"))


def _up(n=300):
    return [_c(i*3600, 100 + i*2) for i in range(n)]


def _down(n=300):
    return [_c(i*3600, 700 - i*2) for i in range(n)]


def _choppy(n=300):
    return [_c(i*3600, 100 + (i % 3)) for i in range(n)]


class TestResample:
    def test_4h_aggregation(self):
        c1h = [_c(i*3600, 100 + i) for i in range(8)]
        c4h = resample_4h(c1h)
        assert len(c4h) == 2
        assert c4h[0].open == c1h[0].open
        assert c4h[0].close == c1h[3].close
        assert c4h[0].high == max(c.high for c in c1h[0:4])
        assert c4h[0].low == min(c.low for c in c1h[0:4])

    def test_incomplete_tail_dropped(self):
        c1h = [_c(i*3600, 100 + i) for i in range(7)]
        assert len(resample_4h(c1h)) == 1


class TestMultiTF:
    def test_uptrend_both(self):
        assert detect_regime_multi_tf(_up(300), SarvRouterConfig()) == Regime.UPTREND

    def test_downtrend_both(self):
        assert detect_regime_multi_tf(_down(300), SarvRouterConfig()) == Regime.DOWNTREND

    def test_choppy_not_uptrend(self):
        r = detect_regime_multi_tf(_choppy(300), SarvRouterConfig())
        assert r in (Regime.RANGE, Regime.UNKNOWN)

    def test_insufficient(self):
        assert detect_regime_multi_tf(_up(20), SarvRouterConfig()) == Regime.UNKNOWN

    def test_disagreement_not_uptrend(self):
        strong = [_c(i*3600, 100 + i*2) for i in range(200)]
        flat = [_c((200+i)*3600, 500 + (i % 2)) for i in range(100)]
        assert detect_regime_multi_tf(strong + flat, SarvRouterConfig()) != Regime.UPTREND


class TestDecideRegimeMultiTF:
    """Phase 1J.2: pure decision logic — soft veto per architect review."""

    def test_both_same_returns_same(self):
        from app.services.bots.sarv_router.regime import _decide_regime_multi_tf
        assert _decide_regime_multi_tf(Regime.UPTREND, Regime.UPTREND) == Regime.UPTREND
        assert _decide_regime_multi_tf(Regime.DOWNTREND, Regime.DOWNTREND) == Regime.DOWNTREND
        assert _decide_regime_multi_tf(Regime.RANGE, Regime.RANGE) == Regime.RANGE
        assert _decide_regime_multi_tf(Regime.UNKNOWN, Regime.UNKNOWN) == Regime.UNKNOWN

    def test_strong_veto_returns_unknown(self):
        """UP vs DOWN → strong veto → UNKNOWN."""
        from app.services.bots.sarv_router.regime import _decide_regime_multi_tf
        assert _decide_regime_multi_tf(Regime.UPTREND, Regime.DOWNTREND) == Regime.UNKNOWN
        assert _decide_regime_multi_tf(Regime.DOWNTREND, Regime.UPTREND) == Regime.UNKNOWN

    def test_uptrend_1h_range_4h_returns_range(self):
        """KEY CHANGE: 1h=UP + 4h=RANGE → RANGE (not UNKNOWN, not UPTREND)."""
        from app.services.bots.sarv_router.regime import _decide_regime_multi_tf
        assert _decide_regime_multi_tf(Regime.UPTREND, Regime.RANGE) == Regime.RANGE

    def test_downtrend_1h_range_4h_returns_range(self):
        """1h=DOWN + 4h=RANGE → RANGE."""
        from app.services.bots.sarv_router.regime import _decide_regime_multi_tf
        assert _decide_regime_multi_tf(Regime.DOWNTREND, Regime.RANGE) == Regime.RANGE

    def test_uptrend_1h_unknown_4h_returns_uptrend(self):
        """1h=UP + 4h=UNKNOWN (insufficient data) → UP (trust 1h)."""
        from app.services.bots.sarv_router.regime import _decide_regime_multi_tf
        assert _decide_regime_multi_tf(Regime.UPTREND, Regime.UNKNOWN) == Regime.UPTREND

    def test_range_1h_uptrend_4h_returns_range(self):
        """1h=RANGE + 4h=UP → RANGE (4h alone not enough)."""
        from app.services.bots.sarv_router.regime import _decide_regime_multi_tf
        assert _decide_regime_multi_tf(Regime.RANGE, Regime.UPTREND) == Regime.RANGE
