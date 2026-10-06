"""UseCase: اسکن مارکت‌ها و امتیازدهی نوسان."""

import asyncio
from dataclasses import dataclass

from app.domain.entities.market import Market
from app.domain.entities.scanned_symbol import ScannedSymbol
from app.domain.ports.exchange import ExchangePort
from app.services.volatility_scorer import calculate_score


@dataclass(slots=True)
class ScanMarketsUseCase:
    """اسکن مارکت‌ها با امتیاز نوسان."""

    exchange: ExchangePort
    max_concurrent: int = 10
    top_n: int = 30

    async def execute(
        self,
        quote: str = "TMN",
        timeframe: str = "1h",
        min_score: float = 0.0,
    ) -> list[ScannedSymbol]:
        """اسکن همه مارکت‌ها."""
        # ۱. دریافت مارکت‌ها
        markets = await self.exchange.get_markets()
        
        # ۲. فیلتر
        quote_upper = quote.upper()
        filtered = [
            m for m in markets
            if str(m.symbol).upper().endswith(quote_upper)
            and getattr(m, "stats", None) is not None
        ]
        
        # ۳. مرتب‌سازی بر اساس حجم
        filtered.sort(
            key=lambda m: float(getattr(m.stats, "daily_quote_volume", 0) or 0),
            reverse=True,
        )
        
        # ۴. اسکن top_n
        top = filtered[: self.top_n]
        
        # ۵. اسکن موازی
        sem = asyncio.Semaphore(self.max_concurrent)
        tasks = [
            self._scan_one(m, sem, timeframe, min_score)
            for m in top
        ]
        results = await asyncio.gather(*tasks)
        
        # ۶. فیلتر None و مرتب‌سازی بر اساس امتیاز
        scanned = [r for r in results if r is not None]
        scanned.sort(key=lambda s: s.score.total_score, reverse=True)
        
        return scanned

    async def _scan_one(
        self,
        market: Market,
        sem: asyncio.Semaphore,
        timeframe: str,
        min_score: float,
    ) -> ScannedSymbol | None:
        """اسکن یک نماد."""
        async with sem:
            try:
                from app.application.use_cases.get_candles import GetCandlesUseCase
                
                symbol = str(market.symbol)
                uc = GetCandlesUseCase(exchange=self.exchange)
                candles = await uc.execute(
                    symbol=symbol,
                    timeframe=timeframe,
                    limit=200,
                )
                
                if not candles or len(candles) < 100:
                    return None
                
                score = calculate_score(symbol, candles)
                if score is None:
                    return None
                
                if score.total_score < min_score:
                    return None
                
                stats = getattr(market, "stats", None)
                
                return ScannedSymbol(
                    symbol=symbol,
                    current_price=candles[-1].close,
                    score=score,
                    volume_24h=getattr(stats, "daily_quote_volume", None) if stats else None,
                    change_24h=getattr(stats, "daily_change_percent", None) if stats else None,
                    timeframe=timeframe,
                )
            except Exception:
                return None
