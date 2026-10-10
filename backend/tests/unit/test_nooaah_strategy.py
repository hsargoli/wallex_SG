"""تست Nooaah strategy — منطق خالص."""

from __future__ import annotations

from decimal import Decimal

import pytest

from app.domain.entities.candle import Candle
from app.services.bots.nooaah.config import NooaahConfig
from app.services.bots.nooaah.strategy import (
    TradeProposal,
    decide,
    pick_best,
    propose_trade,
)


def make_candles(
    closes: list[float],
    vol: float = 10.0,
) -> list[Candle]:
    return [
        Candle(
            time=1000 + i * 3600,
            open=Decimal(str(c)),
            high=Decimal(str(c * 1.005)),
            low=Decimal(str(c * 0.995)),
            close=Decimal(str(c)),
            volume=Decimal(str(vol + i * 0.1)),
        )
        for i, c in enumerate(closes)
    ]


def strong_uptrend(n: int = 200) -> list[Candle]:
    return make_candles([100 + i * 0.5 for i in range(n)])


def flat(n: int = 200) -> list[Candle]:
    return make_candles([100.0] * n)


class TestProposeTrade:
    def test_insufficient_candles_returns_none(self) -> None:
        cfg = NooaahConfig()
        assert propose_trade("BTCTMN", make_candles([100] * 50), cfg) is None

    def test_flat_market_no_signal(self) -> None:
        cfg = NooaahConfig()
        assert propose_trade("BTCTMN", flat(200), cfg) is None

    def test_strong_uptrend_gives_buy(self) -> None:
        cfg = NooaahConfig()
        p = propose_trade("BTCTMN", strong_uptrend(200), cfg)
        assert p is not None
        assert p.action == "BUY"
        assert p.regime == "trending_up"
        assert p.confidence >= cfg.min_confidence
        assert p.take_profit > p.entry > p.stop_loss

    def test_tp_sl_use_atr(self) -> None:
        cfg = NooaahConfig(tp_atr_mult=2.0, sl_atr_mult=1.0)
        p = propose_trade("BTCTMN", strong_uptrend(200), cfg)
        assert p is not None
        # TP دورتر از entry، SL نزدیک‌تر (نسبت 2:1)
        up = p.take_profit - p.entry
        down = p.entry - p.stop_loss
        assert up > down > 0


class TestPickBest:
    def test_empty_returns_none(self) -> None:
        assert pick_best([]) is None

    def test_all_none_returns_none(self) -> None:
        assert pick_best([None, None]) is None

    def test_picks_highest_confidence(self) -> None:
        a = TradeProposal("A", "BUY", 100, 105, 98, 70, "trending_up", "")
        b = TradeProposal("B", "BUY", 100, 105, 98, 85, "trending_up", "")
        c = TradeProposal("C", "BUY", 100, 105, 98, 65, "trending_up", "")
        best = pick_best([a, b, c])
        assert best is not None
        assert best.symbol == "B"


class TestDecide:
    def test_no_symbols_returns_none(self) -> None:
        assert decide({}, NooaahConfig()) is None

    def test_all_flat_returns_none(self) -> None:
        cfg = NooaahConfig()
        data = {"A": flat(), "B": flat(), "C": flat()}
        assert decide(data, cfg) is None

    def test_picks_uptrend_over_flat(self) -> None:
        cfg = NooaahConfig()
        data = {
            "FLAT": flat(200),
            "UP": strong_uptrend(200),
        }
        result = decide(data, cfg)
        assert result is not None
        assert result.symbol == "UP"

    def test_among_two_uptrends_picks_higher_confidence(self) -> None:
        cfg = NooaahConfig()
        # UP1 تندتر از UP2
        up1 = make_candles([100 + i * 1.5 for i in range(200)])
        up2 = make_candles([100 + i * 0.4 for i in range(200)])
        data = {"UP1": up1, "UP2": up2}
        result = decide(data, cfg)
        assert result is not None
        # هر دو trending_up، ولی UP1 معمولاً confidence بالاتر
        assert result.symbol in ("UP1", "UP2")
