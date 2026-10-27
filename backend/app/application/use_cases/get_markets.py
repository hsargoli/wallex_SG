"""UseCase: دریافت لیست مارکت‌های والکس."""
from app.domain.entities.market import Market
from app.domain.ports.exchange import ExchangePort
from app.infrastructure.cache.markets import cache as _markets_cache

class GetMarketsUseCase:
    def __init__(self, exchange: ExchangePort):
        self.exchange = exchange

    async def execute(self) -> list[Market]:
        cached = _markets_cache.get()
        if cached is not None:
            return cached

        markets = await self.exchange.get_markets()
        _markets_cache.set(markets)
        return markets
