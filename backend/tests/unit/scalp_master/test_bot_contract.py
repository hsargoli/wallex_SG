"""Characterization tests: scalp_master contract (M1, M3, M4, M7, M8).

Locks Monitor-mode behavior before paper mode is added.
Zero production changes. If any test is RED → real bug exists.
"""
from decimal import Decimal

from app.domain.entities.candle import Candle
from app.services.bots.base import BotStatus
from app.services.bots.scalp_master.bot import ScalpMasterBot


def _candle(i: int, base: float = 100.0) -> Candle:
    """Candle with slight variation (avoids flat-data edge cases in RSI/ATR)."""
    p = Decimal(str(base + (i % 5) - 2))
    return Candle(
        time=1000 + i,
        open=p,
        high=p + Decimal("1"),
        low=p - Decimal("1"),
        close=p,
        volume=Decimal("10"),
    )


class TestBotContract:
    """M1, M3, M4 — identity & state management (pure, no I/O)."""

    def test_info_contract(self):
        """M1: BotInfo must reflect monitor-only nature."""
        bot = ScalpMasterBot()
        info = bot.info
        assert info.slug == "scalp_master"
        assert info.name_en == "Scalp Master Bot"
        assert info.version == "0.1.0"
        assert "monitor" in info.capabilities
        assert "signal" in info.capabilities
        assert "display" in info.capabilities
        # CRITICAL: monitor-only contract — no trade capabilities
        assert "paper" not in info.capabilities
        assert "live" not in info.capabilities

    def test_reset_clears_state(self):
        """M3: reset() must return bot to fresh IDLE state."""
        bot = ScalpMasterBot()
        bot.state.is_running = True
        bot.state.check_count = 42
        bot.state.recent_signals = [{"x": 1}]
        bot._status = BotStatus.RUNNING

        result = bot.reset()

        assert result == {"status": "reset"}
        assert bot.state.is_running is False
        assert bot.state.check_count == 0
        assert bot.state.recent_signals == []
        assert bot.status == BotStatus.IDLE

    def test_set_symbols_max_two(self):
        """M4: set_symbols must reject empty and > 2."""
        bot = ScalpMasterBot()
        assert bot.set_symbols([])["status"] == "error"
        assert bot.set_symbols(["A", "B", "C"])["status"] == "error"
        r = bot.set_symbols(["X", "Y"])
        assert r["status"] == "ok"
        assert bot.config.symbols == ["X", "Y"]


class TestBotDecision:
    """M7, M8 — diagnose & make_decision (pure, no I/O)."""

    def test_diagnose_entry_returns_checks(self):
        """M7: warmup-only on short data; full 7 checks on long data."""
        bot = ScalpMasterBot()
        cfg = bot.config

        short = [_candle(i) for i in range(10)]
        checks_short = bot.diagnose("X", short)
        assert len(checks_short) == 1
        assert checks_short[0]["name"] == "warmup"
        assert checks_short[0]["passed"] is False

        long = [_candle(i) for i in range(cfg.warmup_candles + 5)]
        checks_long = bot.diagnose("X", long)
        names = {c["name"] for c in checks_long}
        expected = {"liquidity", "drop", "green", "rsi", "body", "atr", "ema"}
        assert expected.issubset(names), f"missing: {expected - names}"

    def test_make_decision_none_when_no_signal(self):
        """M8: insufficient candles → evaluate_entry None → make_decision None."""
        bot = ScalpMasterBot()
        short = [_candle(i) for i in range(5)]
        assert bot.make_decision("X", short) is None
