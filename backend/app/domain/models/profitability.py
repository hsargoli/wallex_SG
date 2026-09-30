"""Pydantic models for profitability analysis."""

from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field

OrderType = Literal["maker", "taker"]


class FeeConfig(BaseModel):
    """Fee configuration for maker/taker orders."""

    maker_fee_rate: Decimal = Field(
        default=Decimal("0.001"),
        ge=0,
        lt=1,
        description="Maker fee rate as decimal (0.001 = 0.1%)",
    )
    taker_fee_rate: Decimal = Field(
        default=Decimal("0.0015"),
        ge=0,
        lt=1,
        description="Taker fee rate as decimal (0.0015 = 0.15%)",
    )


class ProfitabilityRequest(BaseModel):
    """Request to evaluate profitability of a potential trade."""

    symbol: str = Field(..., min_length=1, description="Market symbol, e.g. XRPTMN")
    order_type: OrderType = Field(
        default="maker",
        description="Order type: maker (limit) or taker (market)",
    )
    capital: Decimal = Field(
        ...,
        gt=0,
        description="Capital to deploy in base currency units (e.g. TMN)",
    )
    slippage_pct: Decimal = Field(
        default=Decimal("0"),
        ge=0,
        le=100,
        description="Expected slippage in percent (only for taker orders)",
    )
    maker_fee_rate: Decimal | None = Field(
        default=None,
        ge=0,
        lt=1,
        description="Override maker fee rate for this request",
    )
    taker_fee_rate: Decimal | None = Field(
        default=None,
        ge=0,
        lt=1,
        description="Override taker fee rate for this request",
    )


class ProfitabilityResponse(BaseModel):
    """Result of a profitability analysis."""

    symbol: str
    order_type: OrderType

    # Market data snapshot
    best_bid: Decimal
    best_ask: Decimal
    spread: Decimal
    spread_pct: Decimal

    # Assumptions used
    capital: Decimal
    applied_fee_rate: Decimal
    slippage_pct: Decimal

    # Cost breakdown
    effective_buy_price: Decimal
    effective_sell_price: Decimal
    gross_profit: Decimal
    buy_fee: Decimal
    sell_fee: Decimal
    slippage_cost: Decimal
    total_cost: Decimal

    # Outcome
    net_profit: Decimal
    net_profit_pct: Decimal
    min_profitable_spread: Decimal
    is_profitable: bool

    # Diagnostics
    notes: list[str] = Field(default_factory=list)
