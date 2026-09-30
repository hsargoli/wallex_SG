"""UseCase: دریافت یک مارکت مشخص."""

from dataclasses import dataclass

from app.domain.entities.market import Market
from app.domain.ports.exchange import ExchangePort


@dataclass(slots=True)
class GetMarketUseCase:
    exchange: ExchangePort

    async def execute(self, symbol: str) -> Market:
        return await self.exchange.get_market(symbol)
