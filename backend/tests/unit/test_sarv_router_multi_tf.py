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
