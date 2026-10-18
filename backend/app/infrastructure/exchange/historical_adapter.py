"""Historical Exchange Adapter — serves local CSV data as if it were the Exchange."""
from typing import List, Optional
from app.domain.entities.candle import Candle
from app.domain.ports.exchange import ExchangePort
from app.application.use_cases.historical_loader import HistoricalCandleLoader


class HistoricalExchangeAdapter(ExchangePort):
    """
    A drop-in replacement for ExchangePort that reads from local CSVs.
    Used exclusively for backtesting over long historical periods.
    """
    def __init__(self, start_date: str, end_date: str):
        self.start_date = start_date
        self.end_date = end_date
        self.loader = HistoricalCandleLoader()

    async def get_candles(
        self, 
        symbol: str, 
        resolution: str = "60", 
        from_ts: Optional[int] = None, 
        to_ts: Optional[int] = None,
        **kwargs
    ) -> List[Candle]:
        # We ignore resolution, from_ts, to_ts because GetCandlesUseCase
        # calculates them based on "now", not our historical range.
        # The loader uses self.start_date and self.end_date.
        return self.loader.load(
            symbol=symbol, 
            start_date=self.start_date, 
            end_date=self.end_date, 
            timeframe="1h" # We only have 1h data locally for now
        )

    # Placeholder implementations for other methods
    async def get_markets(self): raise NotImplementedError
    async def get_market(self, symbol: str): raise NotImplementedError
    async def get_balances(self): raise NotImplementedError
    async def place_order(self, *args, **kwargs): raise NotImplementedError
    async def cancel_order(self, *args, **kwargs): raise NotImplementedError
    async def get_order_book(self, *args, **kwargs): raise NotImplementedError
