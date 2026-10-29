"""Phase 2C: Wait for Confirmation — watchlist entry logic."""
from decimal import Decimal
from app.domain.entities.candle import Candle
from app.services.bots.scalp_master.config import ScalpMasterConfig


def _c(t, o, h, l, c, v="100"):
    return Candle(time=t, open=Decimal(str(o)), high=Decimal(str(h)),
                  low=Decimal(str(l)), close=Decimal(str(c)),
                  volume=Decimal(str(v)))


def _down_trend(n=100, top=200.0, drop_pct=3.0):
    """99 flat candles at top, then one sharp crash candle (-drop_pct)."""
    end = top * (1 - drop_pct / 100)
    candles = []
    for i in range(n - 1):
        candles.append(_c(i * 3600, top, top + 0.5, top - 0.5, top))
    candles.append(_c((n - 1) * 3600, top, top + 0.5, end - 1, end))
    return candles


class TestWatchlist:
    def test_dip_enters_watchlist_no_position(self):
        """After dip, symbol is in watchlist, no position opened."""
        from app.services.bots.scalp_master.strategy import evaluate_entry_with_watchlist
        cfg = ScalpMasterConfig(watchlist_enabled=True)
        candles = _down_trend(100, top=200.0, drop_pct=3.0)
        watchlist: dict = {}
        sig = evaluate_entry_with_watchlist(
            symbol="BTCTMN", candles=candles, config=cfg,
            watchlist=watchlist, now_ts=candles[-1].time,
        )
        assert sig is None, "should NOT enter yet — only watch"
        assert "BTCTMN" in watchlist
        assert watchlist["BTCTMN"]["candles_since"] == 0

    def test_confirmation_triggers_entry(self):
        """After dip + 2 green candles → entry."""
        from app.services.bots.scalp_master.strategy import evaluate_entry_with_watchlist
        cfg = ScalpMasterConfig(watchlist_enabled=True)
        base = _down_trend(100, top=200.0, drop_pct=3.0)
        watchlist: dict = {}

        # Tick 1: detect dip
        evaluate_entry_with_watchlist("BTCTMN", base, cfg, watchlist, base[-1].time)
        assert "BTCTMN" in watchlist

        # Tick 2: first green candle
        last = base[-1]
        green1 = _c(last.time + 3600, float(last.close), float(last.close) + 2,
                    float(last.close) - 0.5, float(last.close) + 1.5)
        candles2 = base + [green1]
        sig2 = evaluate_entry_with_watchlist("BTCTMN", candles2, cfg, watchlist, green1.time)
        assert sig2 is None, "1 green candle is not enough"

        # Tick 3: second green candle (rising)
        green2 = _c(green1.time + 3600, float(green1.close), float(green1.close) + 2,
                    float(green1.close) - 0.5, float(green1.close) + 1.5)
        candles3 = candles2 + [green2]
        sig3 = evaluate_entry_with_watchlist("BTCTMN", candles3, cfg, watchlist, green2.time)
        assert sig3 is not None, "2 green candles should trigger entry"
        assert "BTCTMN" not in watchlist, "removed after entry"

    def test_timeout_removes_from_watchlist(self):
        """After 6+ candles without confirmation → remove."""
        from app.services.bots.scalp_master.strategy import evaluate_entry_with_watchlist
        cfg = ScalpMasterConfig(watchlist_enabled=True, watchlist_max_candles=6)
        base = _down_trend(100, top=200.0, drop_pct=3.0)
        watchlist: dict = {}
        evaluate_entry_with_watchlist("BTCTMN", base, cfg, watchlist, base[-1].time)
        assert "BTCTMN" in watchlist

        # 7 neutral candles (no green)
        last = base[-1]
        for i in range(7):
            nxt = _c(last.time + (i + 1) * 3600, float(last.close),
                     float(last.close) + 0.5, float(last.close) - 0.5, float(last.close))
            base = base + [nxt]
            evaluate_entry_with_watchlist("BTCTMN", base, cfg, watchlist, nxt.time)
        assert "BTCTMN" not in watchlist, "should timeout after max_candles"

    def test_further_drop_removes_from_watchlist(self):
        """If price drops another 2%+ → remove (falling knife too sharp)."""
        from app.services.bots.scalp_master.strategy import evaluate_entry_with_watchlist
        cfg = ScalpMasterConfig(watchlist_enabled=True, watchlist_extra_drop_pct=2.0)
        base = _down_trend(100, top=200.0, drop_pct=3.0)
        watchlist: dict = {}
        evaluate_entry_with_watchlist("BTCTMN", base, cfg, watchlist, base[-1].time)
        detected = float(base[-1].close)
        assert "BTCTMN" in watchlist

        # Price drops another 2.5% below detected
        crash = detected * (1 - 0.025)
        crash_c = _c(base[-1].time + 3600, crash, crash + 0.1, crash - 0.1, crash)
        base2 = base + [crash_c]
        evaluate_entry_with_watchlist("BTCTMN", base2, cfg, watchlist, crash_c.time)
        assert "BTCTMN" not in watchlist, "further drop should remove from watchlist"
