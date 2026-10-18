"""Historical Exchange Adapter — serves local CSV data as if it were the Exchange."""
from typing import List
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

    async def get_candles(self, symbol: str, timeframe: str = "1h", limit: int = 3000) -> List[Candle]:
        # Ignore limit, load exactly the requested date range
        return self.loader.load(
            symbol=symbol, 
            start_date=self.start_date, 
            end_date=self.end_date, 
            timeframe=timeframe
        )

    # Placeholder implementations for other methods (not needed for backtest)
    async def get_markets(self): raise NotImplementedError("HistoricalAdapter does not support get_markets")
    async def get_market(self, symbol: str): raise NotImplementedError("HistoricalAdapter does not support get_market")
    async def get_balances(self): raise NotImplementedError("HistoricalAdapter does not support get_balances")
    async def place_order(self, *args, **kwargs): raise NotImplementedError("HistoricalAdapter does not support place_order")
    async def cancel_order(self, *args, **kwargs): raise NotImplementedError("HistoricalAdapter does not support cancel_order")
    async def get_order_book(self, *args, **kwargs): raise NotImplementedError("HistoricalAdapter does not support get_order_book")
