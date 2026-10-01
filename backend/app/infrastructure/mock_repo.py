from app.domain.repository import MarketDataRepository
from typing import List

class MockMarketData(MarketDataRepository):
    def get_prices(self, symbol: str, start_date: str, end_date: str) -> List[float]:
        # This will be replaced by DB access later
        return [99.0, 100.5, 101.5, 98.0, 102.0]
