"""Unit tests for ProfitabilityService math."""

from decimal import Decimal

import pytest

from app.domain.models.profitability import (
    FeeConfig,
    ProfitabilityRequest,
)
from app.services.profitability_service import ProfitabilityService


class TestBasicMath:
    def test_break_even_when_zero_fees_and_zero_spread(self):
        svc = ProfitabilityService(
            FeeConfig(maker_fee_rate=Decimal("0"), taker_fee_rate=Decimal("0"))
        )
        req = ProfitabilityRequest(
            symbol="XRPTMN",
            order_type="maker",
            capital=Decimal("1000000"),
        )
        result = svc.evaluate(request=req, best_bid=Decimal("100"), best_ask=Decimal("100"))
        assert result.net_profit == Decimal("0.00000000")
        assert result.is_profitable is False

    def test_profitable_when_spread_exceeds_fees(self):
        svc = ProfitabilityService(
            FeeConfig(maker_fee_rate=Decimal("0.0001"), taker_fee_rate=Decimal("0.0002"))
        )
        req = ProfitabilityRequest(
            symbol="XRPTMN",
            order_type="maker",
            capital=Decimal("1000000"),
        )
        # spread = 1 on price ~100 → 1% spread, fee 0.01% → profitable
        result = svc.evaluate(request=req, best_bid=Decimal("100"), best_ask=Decimal("101"))
        assert result.is_profitable is True
        assert result.net_profit > 0

    def test_unprofitable_when_fees_exceed_spread(self):
        svc = ProfitabilityService(
            FeeConfig(maker_fee_rate=Decimal("0.01"), taker_fee_rate=Decimal("0.02"))
        )
        req = ProfitabilityRequest(
            symbol="XRPTMN",
            order_type="maker",
            capital=Decimal("1000000"),
        )
        # spread = 0.01 on price 100 → 0.01% spread, fee 1% → unprofitable
        result = svc.evaluate(request=req, best_bid=Decimal("100"), best_ask=Decimal("100.01"))
        assert result.is_profitable is False
        assert result.net_profit < 0


class TestMakerVsTaker:
    def test_maker_uses_maker_fee(self):
        svc = ProfitabilityService(
            FeeConfig(maker_fee_rate=Decimal("0.0001"), taker_fee_rate=Decimal("0.001"))
        )
        req = ProfitabilityRequest(symbol="XRPTMN", order_type="maker", capital=Decimal("1000000"))
        result = svc.evaluate(request=req, best_bid=Decimal("100"), best_ask=Decimal("100.5"))
        assert result.applied_fee_rate == Decimal("0.0001")

    def test_taker_uses_taker_fee(self):
        svc = ProfitabilityService(
            FeeConfig(maker_fee_rate=Decimal("0.0001"), taker_fee_rate=Decimal("0.001"))
        )
        req = ProfitabilityRequest(symbol="XRPTMN", order_type="taker", capital=Decimal("1000000"))
        result = svc.evaluate(request=req, best_bid=Decimal("100"), best_ask=Decimal("100.5"))
        assert result.applied_fee_rate == Decimal("0.001")

    def test_per_request_fee_override(self):
        svc = ProfitabilityService(FeeConfig(maker_fee_rate=Decimal("0.001")))
        req = ProfitabilityRequest(
            symbol="XRPTMN",
            order_type="maker",
            capital=Decimal("1000000"),
            maker_fee_rate=Decimal("0.0002"),
        )
        result = svc.evaluate(request=req, best_bid=Decimal("100"), best_ask=Decimal("101"))
        assert result.applied_fee_rate == Decimal("0.0002")


class TestSlippage:
    def test_maker_ignores_slippage(self):
        svc = ProfitabilityService(FeeConfig(maker_fee_rate=Decimal("0")))
        req = ProfitabilityRequest(
            symbol="XRPTMN",
            order_type="maker",
            capital=Decimal("1000000"),
            slippage_pct=Decimal("0.5"),
        )
        result = svc.evaluate(request=req, best_bid=Decimal("100"), best_ask=Decimal("101"))
        assert result.slippage_pct == Decimal("0")
        # maker should buy at bid exactly
        assert result.effective_buy_price == Decimal("100.00000000")

    def test_taker_applies_slippage_to_buy_and_sell(self):
        svc = ProfitabilityService(FeeConfig(taker_fee_rate=Decimal("0")))
        req = ProfitabilityRequest(
            symbol="XRPTMN",
            order_type="taker",
            capital=Decimal("1000000"),
            slippage_pct=Decimal("1"),
        )
        result = svc.evaluate(request=req, best_bid=Decimal("100"), best_ask=Decimal("102"))
        # buy at 102 * 1.01 = 103.02
        assert result.effective_buy_price == Decimal("103.02000000")
        # sell at 100 * 0.99 = 99
        assert result.effective_sell_price == Decimal("99.00000000")
        # with such slippage, trade is deeply unprofitable
        assert result.is_profitable is False


class TestMinProfitableSpread:
    def test_min_spread_reflects_fee_rate(self):
        svc = ProfitabilityService(FeeConfig(maker_fee_rate=Decimal("0.001")))
        req = ProfitabilityRequest(symbol="XRPTMN", order_type="maker", capital=Decimal("1000000"))
        result = svc.evaluate(request=req, best_bid=Decimal("100"), best_ask=Decimal("100.5"))
        # (ask + bid) * fee_rate = 200.5 * 0.001 = 0.2005
        assert result.min_profitable_spread == Decimal("0.20050000")

    def test_spread_below_min_is_unprofitable(self):
        svc = ProfitabilityService(FeeConfig(maker_fee_rate=Decimal("0.001")))
        req = ProfitabilityRequest(symbol="XRPTMN", order_type="maker", capital=Decimal("1000000"))
        result = svc.evaluate(request=req, best_bid=Decimal("100"), best_ask=Decimal("100.1"))
        # spread = 0.1 < min_profitable_spread ≈ 0.2001
        assert result.is_profitable is False


class TestDecimalPrecision:
    def test_no_float_artifacts(self):
        svc = ProfitabilityService(FeeConfig(maker_fee_rate=Decimal("0")))
        req = ProfitabilityRequest(symbol="XRPTMN", order_type="maker", capital=Decimal("0.1"))
        result = svc.evaluate(request=req, best_bid=Decimal("0.1"), best_ask=Decimal("0.2"))
        # 0.1 / 0.1 = 1, spread 0.1 → profit 0.1
        assert result.gross_profit == Decimal("0.10000000")


class TestValidation:
    def test_negative_bid_raises(self):
        svc = ProfitabilityService()
        req = ProfitabilityRequest(symbol="XRPTMN", order_type="maker", capital=Decimal("1000"))
        with pytest.raises(ValueError, match="must be positive"):
            svc.evaluate(request=req, best_bid=Decimal("-1"), best_ask=Decimal("100"))

    def test_ask_less_than_bid_raises(self):
        svc = ProfitabilityService()
        req = ProfitabilityRequest(symbol="XRPTMN", order_type="maker", capital=Decimal("1000"))
        with pytest.raises(ValueError, match="greater than or equal"):
            svc.evaluate(request=req, best_bid=Decimal("100"), best_ask=Decimal("99"))
