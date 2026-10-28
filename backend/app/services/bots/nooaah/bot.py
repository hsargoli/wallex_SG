"""Nooaah Bot — orchestration.

منطق خالص در strategy.py. این فایل فقط:
  - لیست نمادهای پرحجم رو می‌گیره
  - candles هر کدوم رو fetch می‌کنه
  - به strategy.decide می‌ده
  - نتیجه رو ذخیره/برمی‌گردونه

توجه: طبق ADR-0008، این ربات «مصرف‌کننده‌ی analysis engine»ـه — نه صاحبش.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Sequence

import structlog

from app.application.use_cases.get_candles import GetCandlesUseCase
from app.domain.entities.candle import Candle
from app.domain.ports.exchange import ExchangePort
from app.services.bots.nooaah.config import NooaahConfig
from app.services.bots.nooaah.strategy import TradeProposal, decide
from app.services.bots.base import BaseBot, BotInfo, BotStatus

log = structlog.get_logger("nooaah.bot")


@dataclass(slots=True)
class NooaahRunResult:
    """نتیجه‌ی یه اجرای Nooaah."""

    started_at: int
    duration_seconds: float
    symbols_analyzed: list[str]
    proposal: TradeProposal | None
    error: str | None = None


class NooaahBot(BaseBot):
    """ربات Nooaah — انتخاب بهترین نماد trending_up."""

    def __init__(
        self,
        exchange: ExchangePort,
        config: NooaahConfig | None = None,
    ) -> None:
        self._exchange = exchange
        self._config = config or NooaahConfig()
        self._get_candles = GetCandlesUseCase(exchange=exchange)

    async def pick_top_symbols(self, n: int) -> list[str]:
        """n نماد پرحجم (بر اساس daily_quote_volume)."""
        markets = await self._exchange.get_markets()
        ranked = sorted(
            markets,
            key=lambda m: float(m.stats.daily_quote_volume or 0)
            if m.stats and m.stats.daily_quote_volume
            else 0.0,
            reverse=True,
        )
        return [str(m.symbol) for m in ranked[:n]]

    async def fetch_candles(
        self, symbol: str, limit: int
    ) -> list[Candle]:
        """کندل‌های یه نماد."""
        try:
            return await self._get_candles.execute(
                symbol=symbol,
                timeframe="1h",
                limit=limit,
            )
        except Exception as exc:
            log.warning(
                "nooaah.fetch_failed", symbol=symbol, error=str(exc)
            )
            return []

    async def run_once(self) -> NooaahRunResult:
        """یه چرخه: top نمادها → fetch → decide."""
        started = int(time.time())
        t0 = time.monotonic()

        symbols = await self.pick_top_symbols(self._config.top_n)
        log.info("nooaah.top_symbols", symbols=symbols)

        if not symbols:
            return NooaahRunResult(
                started_at=started,
                duration_seconds=time.monotonic() - t0,
                symbols_analyzed=[],
                proposal=None,
                error="no markets returned",
            )

        # fetch موازی
        candles_map: dict[str, Sequence[Candle]] = {}
        results = await asyncio.gather(
            *[self.fetch_candles(s, 500) for s in symbols],
            return_exceptions=False,
        )
        for sym, candles in zip(symbols, results):
            if candles:
                candles_map[sym] = candles

        if not candles_map:
            return NooaahRunResult(
                started_at=started,
                duration_seconds=time.monotonic() - t0,
                symbols_analyzed=[],
                proposal=None,
                error="no candles fetched",
            )

        proposal = decide(candles_map, self._config)
        return NooaahRunResult(
            started_at=started,
            duration_seconds=time.monotonic() - t0,
            symbols_analyzed=list(candles_map.keys()),
            proposal=proposal,
        )

    # --- BaseBot Interface (Minimal Implementation) ---
    @property
    def info(self) -> BotInfo:
        return BotInfo(
            slug="nooaah",
            name="نوح",
            name_en="Nooaah",
            version="1.0.0",
            description="ربات جامع ML و Regime",
            capabilities=["paper", "live", "backtest"],
            tier="production",
        )

    @property
    def status(self) -> BotStatus:
        return BotStatus.RUNNING

    async def start(self, exchange) -> dict:
        return {"status": "started", "message": "Nooaah is managed by runner"}

    async def stop(self) -> dict:
        return {"status": "stopped"}

    def reset(self) -> dict:
        return {"status": "reset"}

    def get_status(self) -> dict:
        return {"slug": "nooaah", "status": "running", "tier": "production"}
