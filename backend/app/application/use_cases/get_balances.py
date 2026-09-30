"""UseCase: دریافت موجودی‌ها."""

from dataclasses import dataclass

from app.domain.entities.balance import Balance
from app.domain.ports.exchange import ExchangePort


@dataclass(slots=True)
class GetBalancesUseCase:
    exchange: ExchangePort

    async def execute(self) -> list[Balance]:
        return await self.exchange.get_balances()
