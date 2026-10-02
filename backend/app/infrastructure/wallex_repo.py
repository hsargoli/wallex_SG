from typing import List
from decimal import Decimal
from datetime import datetime, timezone, timedelta
import requests

from app.domain.repository import MarketDataRepository
from app.domain.entities.candle import Candle

BASE_URL = "https://api.wallex.ir"

# نقشه‌ی تایم‌فریم → resolution در UDF API والکس
TIMEFRAME_TO_RESOLUTION = {
    "1m": "1",
    "5m": "5",
    "15m": "15",
    "30m": "30",
    "1h": "60",
    "4h": "240",
    "1D": "1D",
    "1W": "1W",
}


class WallexMarketData(MarketDataRepository):
    """داده‌ی بازار از API والکس."""

    def __init__(self, timeout: int = 20):
        self.timeout = timeout
        self.session = requests.Session()

    @staticmethod
    def _date_to_ts(date_str: str) -> int:
        dt = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        return int(dt.timestamp())

    # ------------------------------------------------------------
    # متد اصلی: دریافت کندل‌های OHLCV
    # ------------------------------------------------------------
    def get_candles(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        timeframe: str = "1D",
    ) -> List[Candle]:
        """
        دریافت کندل‌ها با تایم‌فریم مشخص.

        Args:
            symbol:     نماد (BTCUSDT)
            start_date: YYYY-MM-DD
            end_date:   YYYY-MM-DD
            timeframe:  "1m" | "5m" | "15m" | "1h" | "4h" | "1D" | "1W"
        """
        resolution = TIMEFRAME_TO_RESOLUTION.get(timeframe, "1D")

        try:
            from_ts = self._date_to_ts(start_date)
            to_dt = (
                datetime.strptime(end_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                + timedelta(days=1)
            )
            to_ts = int(to_dt.timestamp())
        except ValueError as e:
            print(f"⚠️ فرمت تاریخ نامعتبر: {e}")
            return []

        try:
            r = self.session.get(
                f"{BASE_URL}/v1/udf/history",
                params={
                    "symbol": symbol,
                    "resolution": resolution,
                    "from": from_ts,
                    "to": to_ts,
                },
                timeout=self.timeout,
            )
            r.raise_for_status()
            data = r.json()
        except Exception as e:
            print(f"⚠️ خطا در API والکس برای {symbol}: {e}")
            return []

        if data.get("s") != "ok":
            print(f"⚠️ پاسخ غیرموفق از والکس برای {symbol}: {data.get('s')}")
            return []

        times = data.get("t", [])
        opens = data.get("o", [])
        highs = data.get("h", [])
        lows = data.get("l", [])
        closes = data.get("c", [])
        volumes = data.get("v", [])

        n = min(len(times), len(opens), len(highs), len(lows), len(closes), len(volumes))
        candles: List[Candle] = []
        for i in range(n):
            candles.append(Candle(
                time=int(times[i]),
                open=Decimal(str(opens[i])),
                high=Decimal(str(highs[i])),
                low=Decimal(str(lows[i])),
                close=Decimal(str(closes[i])),
                volume=Decimal(str(volumes[i])),
            ))
        return candles

    # ------------------------------------------------------------
    # متد قدیمی: فقط قیمت Close (سازگاری عقب‌رو)
    # ------------------------------------------------------------
    def get_prices(self, symbol: str, start_date: str, end_date: str) -> List[float]:
        candles = self.get_candles(symbol, start_date, end_date, "1D")
        return [float(c.close) for c in candles]
