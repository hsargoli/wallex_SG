"""Market Scanner Bot — اسکنر نمایشی.

ویژگی‌ها:
  - اسکن مداوم بازار
  - شناسایی نمادهای نوسانی
  - ترید نمی‌کند (فقط نمایش)
"""

import asyncio
import time
from dataclasses import dataclass, field

from app.domain.entities.candle import Candle
from app.services.bots.base import BaseBot, BotInfo, BotStatus
from app.services.bots.market_scanner.config import MarketScannerConfig


@dataclass
class ScannerState:
    """State اسکنر."""

    is_running: bool = False
    started_at: int = 0
    last_scan_at: int = 0
    scan_count: int = 0
    last_results: list[dict] = field(default_factory=list)
    _task: asyncio.Task | None = None


class MarketScannerBot(BaseBot):
    """اسکنر بازار — نمایشی، بدون ترید."""

    def __init__(self, config: MarketScannerConfig | None = None):
        self.config = config or MarketScannerConfig()
        self.state = ScannerState()
        self._status = BotStatus.IDLE

    @property
    def info(self) -> BotInfo:
        return BotInfo(
            slug="market_scanner",
            name="اسکنر بازار",
            name_en="Market Scanner Bot",
            version="0.1.0",
            description="اسکن مداوم بازار و شناسایی نمادهای نوسانی — بدون ترید",
            tags=["scanner", "monitor", "volatility", "display"],
            capabilities=["monitor", "scan", "display"],
        )

    @property
    def status(self) -> BotStatus:
        return self._status

    async def start(self, exchange) -> dict:
        """شروع اسکن دوره‌ای."""
        if self.state.is_running:
            return {"status": "already_running"}

        self._status = BotStatus.RUNNING
        self.state.is_running = True
        self.state.started_at = int(time.time())

        # اجرای اولین اسکن
        await self._scan_once(exchange)

        # شروع loop
        self.state._task = asyncio.create_task(self._scan_loop(exchange))

        return {
            "status": "started",
            "bot": "market_scanner",
            "interval_sec": self.config.scan_interval_sec,
        }

    async def stop(self) -> dict:
        """توقف."""
        self._status = BotStatus.STOPPED
        self.state.is_running = False

        if self.state._task and not self.state._task.done():
            self.state._task.cancel()
            try:
                await self.state._task
            except asyncio.CancelledError:
                pass

        return {"status": "stopped"}

    def reset(self) -> dict:
        """ریست."""
        self.state = ScannerState()
        self._status = BotStatus.IDLE
        return {"status": "reset"}

    def get_status(self) -> dict:
        """وضعیت کامل."""
        s = self.state
        return {
            "is_running": s.is_running,
            "started_at": s.started_at,
            "last_scan_at": s.last_scan_at,
            "scan_count": s.scan_count,
            "results_count": len(s.last_results),
            "results": s.last_results,
            "config": {
                "timeframe": self.config.timeframe,
                "available_timeframes": self.config.available_timeframes,
                "top_n": self.config.top_n,
                "min_score": self.config.min_score,
                "scan_interval_sec": self.config.scan_interval_sec,
            },
        }

    def make_decision(self, symbol: str, candles: list[Candle]) -> dict | None:
        """ترید نمی‌کند."""
        return None

    def set_timeframe(self, timeframe: str) -> dict:
        """تغییر تایم‌فریم."""
        if timeframe not in self.config.available_timeframes:
            return {
                "status": "error",
                "message": f"TF نامعتبر. مقادیر مجاز: {self.config.available_timeframes}",
            }
        self.config.timeframe = timeframe
        return {"status": "ok", "timeframe": timeframe}

    async def _scan_once(self, exchange) -> None:
        """یک اسکن."""
        from app.application.use_cases.scan_markets import ScanMarketsUseCase

        try:
            uc = ScanMarketsUseCase(
                exchange=exchange,
                top_n=self.config.top_n,
                max_concurrent=self.config.max_concurrent,
            )
            results = await uc.execute(
                quote=self.config.quote,
                timeframe=self.config.timeframe,
                min_score=self.config.min_score,
            )

            self.state.last_results = [
                {
                    "symbol": s.symbol,
                    "score": s.score.total_score,
                    "atr_pct": s.score.atr_pct,
                    "volume_ratio": s.score.volume_ratio,
                    "price": str(s.current_price),
                }
                for s in results[:50]
            ]
            self.state.last_scan_at = int(time.time())
            self.state.scan_count += 1
        except Exception as e:
            self.state.last_results = [{"error": str(e)[:200]}]

    async def _scan_loop(self, exchange) -> None:
        """Loop اسکن."""
        while self.state.is_running:
            try:
                await asyncio.sleep(self.config.scan_interval_sec)
                if not self.state.is_running:
                    break
                await self._scan_once(exchange)
            except asyncio.CancelledError:
                break
            except Exception:
                await asyncio.sleep(60)
