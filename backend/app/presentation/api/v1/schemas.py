from decimal import Decimal

from pydantic import BaseModel, ConfigDict


# --- Market Schemas ---
class MarketOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    symbol: str
    base_asset: str
    quote_asset: str
    last_price: Decimal | None = None
    fa_name: str | None = None
    en_name: str | None = None


class MarketsResponse(BaseModel):
    count: int
    items: list[MarketOut]


# --- Account Schemas ---
class BalanceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    asset: str
    available: Decimal
    locked: Decimal
    total: Decimal
    fa_name: str | None = None
    en_name: str | None = None


class BalancesResponse(BaseModel):
    count: int
    items: list[BalanceOut]


class KeyBalancesResponse(BaseModel):
    tmn_available: Decimal
    tmn_locked: Decimal
    usdt_available: Decimal
    usdt_locked: Decimal
    xrp_available: Decimal
    xrp_locked: Decimal


class OrderBookLevel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    price: Decimal
    quantity: Decimal
    sum: Decimal | None = None


class OrderBookResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    symbol: str
    best_bid: Decimal | None = None
    best_ask: Decimal | None = None
    spread: Decimal | None = None
    spread_pct: Decimal | None = None
    bids: list[OrderBookLevel] = []
    asks: list[OrderBookLevel] = []


class PortfolioItemOut(BaseModel):
    asset: str
    fa_name: str | None = None
    available: Decimal
    locked: Decimal
    total: Decimal

    price_usdt_bid: Decimal | None = None
    price_usdt_last: Decimal | None = None
    price_tmn_bid: Decimal | None = None
    price_tmn_last: Decimal | None = None

    value_usdt_bid: Decimal | None = None
    value_usdt_last: Decimal | None = None
    value_tmn_bid: Decimal | None = None
    value_tmn_last: Decimal | None = None

    share_pct_bid: Decimal = Decimal("0")
    share_pct_last: Decimal = Decimal("0")

    has_tmn_pair: bool = False
    has_usdt_pair: bool = False


class PortfolioResponse(BaseModel):
    count: int
    total_value_tmn_bid: Decimal
    total_value_tmn_last: Decimal
    total_value_usdt_bid: Decimal
    total_value_usdt_last: Decimal
    usdt_tmn_rate: Decimal | None = None
    items: list[PortfolioItemOut]
