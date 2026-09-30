"""Endpointهای بازار."""

from fastapi import APIRouter

from app.application.use_cases.get_market import GetMarketUseCase
from app.application.use_cases.get_markets import GetMarketsUseCase
from app.domain.entities.market import Market
from app.infrastructure.exchange.wallex.mapper import map_order_book
from app.presentation.api.deps import ExchangeDep
from app.presentation.api.v1.schemas import (
    MarketOut,
    MarketsResponse,
    OrderBookResponse,
)

router = APIRouter(prefix="/markets", tags=["markets"])


def _to_out(m: Market) -> MarketOut:
    data = {
        "symbol": str(m.symbol),
        "base_asset": m.base_asset,
        "quote_asset": m.quote_asset,
        "last_price": m.last_price,
        "fa_name": m.fa_name,
        "en_name": m.en_name,
    }
    return MarketOut.model_validate(data)


@router.get("", response_model=MarketsResponse)
async def list_markets(exchange: ExchangeDep) -> MarketsResponse:
    """دریافت همه مارکت‌های فعال والکس."""
    use_case = GetMarketsUseCase(exchange=exchange)
    markets = await use_case.execute()
    items = [_to_out(m) for m in markets]
    return MarketsResponse(count=len(items), items=items)


@router.get("/{symbol}", response_model=MarketOut)
async def get_market(symbol: str, exchange: ExchangeDep) -> MarketOut:
    """دریافت اطلاعات یک مارکت مشخص."""
    use_case = GetMarketUseCase(exchange=exchange)
    market = await use_case.execute(symbol)
    return _to_out(market)


@router.get("/orderbook/{symbol}", response_model=OrderBookResponse)
async def get_order_book_endpoint(symbol: str, exchange: ExchangeDep):
    """دریافت دفتر سفارشات یک نماد."""
    raw_data = await exchange.get_order_book(symbol=symbol)
    return map_order_book(raw_data, symbol=symbol)
