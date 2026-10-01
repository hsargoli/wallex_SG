from typing import List
from app.domain.repository import MarketDataRepository

class WallexMarketData(MarketDataRepository):
    def get_prices(self, symbol: str, start_date: str, end_date: str) -> List[float]:
        # Return mock price data for logic testing
        return [100.0, 102.5, 98.0, 105.0]
