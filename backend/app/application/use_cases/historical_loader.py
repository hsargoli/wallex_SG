"""Load historical candles from local CSV files."""
import pandas as pd
from decimal import Decimal
from pathlib import Path
from typing import List
from datetime import datetime, timezone

from app.domain.entities.candle import Candle

class HistoricalCandleLoader:
    def __init__(self, data_dir: str = "data/candles/historical"):
        self.data_dir = Path(data_dir)

    def load(self, symbol: str, start_date: str, end_date: str, timeframe: str = "1h") -> List[Candle]:
        # Normalize symbol (e.g., BTCTMN -> BTCUSDT for local files)
        symbol_map = {
            "BTCTMN": "BTCUSDT",
            "ETHTMN": "ETHUSDT",
            "SOLTMN": "SOLUSDT",
        }
        file_symbol = symbol_map.get(symbol, symbol)
        file_path = self.data_dir / f"{file_symbol}_{timeframe}.csv"
        
        if not file_path.exists():
            raise ValueError(f"Local data not found for {file_symbol} {timeframe}")

        df = pd.read_csv(file_path)
        
        # Filter by date
        df['datetime'] = pd.to_datetime(df['open_time'], unit='s', utc=True)
        start_dt = pd.to_datetime(start_date, utc=True)
        end_dt = pd.to_datetime(end_date, utc=True)
        
        df = df[(df['datetime'] >= start_dt) & (df['datetime'] <= end_dt)]
        
        if len(df) < 35:
            raise ValueError(f"Not enough data in range {start_date} to {end_date}")

        candles = []
        for _, row in df.iterrows():
            candles.append(Candle(
                time=int(row['open_time']),
                open=Decimal(str(row['open'])),
                high=Decimal(str(row['high'])),
                low=Decimal(str(row['low'])),
                close=Decimal(str(row['close'])),
                volume=Decimal(str(row['volume']))
            ))
        return candles
