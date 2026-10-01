from abc import ABC, abstractmethod
from typing import List

class MarketDataRepository(ABC):
    @abstractmethod
    def get_prices(self, symbol: str, start_date: str, end_date: str) -> List[float]:
        pass
