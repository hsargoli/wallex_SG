"""UseCase: دریافت همه مارکت‌ها."""

from dataclasses import dataclass

from app.domain.entities.market import Market
from app.domain.ports.exchange import ExchangePort


@dataclass(slots=True)
class GetMarketsUseCase:
    exchange: ExchangePort

    async def execute(self) -> list[Market]:
        return await self.exchange.get_markets()
