"""WallexExchange — پیاده‌سازی ExchangePort برای صرافی والکس."""

from __future__ import annotations

from types import TracebackType
from typing import Any, Self

import httpx
import structlog

from app.core.config import Settings
from app.domain.entities.balance import Balance
from app.domain.entities.candle import Candle
from app.domain.entities.market import Market
from app.domain.exceptions import (
    ExchangeAuthError,
    ExchangeError,
    ExchangeRateLimitError,
    ExchangeUnavailableError,
    InvalidSymbolError,
)
from app.infrastructure.exchange.wallex.mapper import map_balance, map_candles, map_market


class WallexExchange:
    """Adapter صرافی والکس — پیاده‌ساز ExchangePort."""

    def __init__(self, settings: Settings, client: httpx.AsyncClient) -> None:
        self._settings = settings
        self._client = client
        self._log = structlog.get_logger("wallex.exchange")

    @classmethod
    def create(cls, settings: Settings) -> WallexExchange:
        """ساخت با Connection Pool اختصاصی."""
        limits = httpx.Limits(
            max_connections=settings.WALLEX_MAX_CONNECTIONS,
            max_keepalive_connections=settings.WALLEX_MAX_CONNECTIONS // 2,
        )
        client = httpx.AsyncClient(
            base_url=settings.WALLEX_BASE_URL,
            headers={"x-api-key": settings.WALLEX_API_KEY},
            timeout=httpx.Timeout(settings.WALLEX_TIMEOUT_SECONDS),
            limits=limits,
            http2=False,
        )
        return cls(settings, client)

    async def aclose(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        await self.aclose()

    # ---------- Internal HTTP ----------

    async def _get(self, path: str, **params: Any) -> dict[str, Any]:
        try:
            r = await self._client.get(path, params=params or None)
        except httpx.TimeoutException as e:
            raise ExchangeUnavailableError(f"Timeout: {path}") from e
        except httpx.HTTPError as e:
            raise ExchangeUnavailableError(f"Network error: {e}") from e

        if r.status_code == 401:
            raise ExchangeAuthError("کلید API نامعتبر است")
        if r.status_code == 429:
            raise ExchangeRateLimitError("Rate Limit والکس")
        if r.status_code >= 500:
            raise ExchangeUnavailableError(f"Wallex {r.status_code}")
        if r.status_code >= 400:
            raise ExchangeError(
                f"Wallex {r.status_code}: {r.text[:200]}",
                code="exchange_bad_request",
            )

        try:
            payload = r.json()
        except ValueError as e:
            raise ExchangeError("پاسخ والکس JSON معتبر نیست") from e

        if not payload.get("success", True):
            msg = payload.get("message") or "Unknown error from Wallex"
            raise ExchangeError(msg, code="exchange_error")

        return payload

    # ---------- ExchangePort ----------

    async def get_markets(self) -> list[Market]:
        payload = await self._get("/v1/markets")
        symbols = payload.get("result", {}).get("symbols", {})
        markets = [map_market(sym, raw) for sym, raw in symbols.items()]
        self._log.debug("markets_fetched", count=len(markets))
        return markets

    async def get_market(self, symbol: str) -> Market:
        """دریافت یک مارکت مشخص. Wallex فیلتر query param نداره، پس سمت کلاینت فیلتر می‌کنیم."""
        payload = await self._get("/v1/markets")
        symbols = payload.get("result", {}).get("symbols", {})
        symbol_upper = symbol.upper()
        for sym_key, raw in symbols.items():
            if sym_key.upper() == symbol_upper:
                return map_market(sym_key, raw)
        raise InvalidSymbolError(f"نماد {symbol} یافت نشد")

    async def get_balances(self) -> list[Balance]:
        payload = await self._get("/v1/account/balances")
        balances_raw = payload.get("result", {}).get("balances", {})
        return [map_balance(asset, raw) for asset, raw in balances_raw.items()]

    async def health_check(self) -> bool:
        try:
            await self._get("/v1/markets")
            return True
        except ExchangeError:
            return False

    async def get_order_book(self, symbol: str) -> dict:
        """Fetch market depth for a specific symbol from Wallex."""
        response = await self._client.get("/v1/depth", params={"symbol": symbol})
        response.raise_for_status()
        return response.json()

    async def get_candles(
        self,
        symbol: str,
        resolution: str,
        from_ts: int,
        to_ts: int,
    ) -> list[Candle]:
        """دریافت کندل‌های تاریخی از UDF endpoint والکس.

        Args:
            symbol: نماد (مثلاً BTCTMN)
            resolution: تایم‌فریم والکس ('15' برای 1m, '60' برای 1h, 'D' برای 1d)
            from_ts: شروع (Unix timestamp ثانیه)
            to_ts: پایان (Unix timestamp ثانیه)
        """
        raw = await self._get(
            "/v1/udf/history",
            symbol=symbol,
            resolution=resolution,
            **{"from": from_ts, "to": to_ts},
        )
        return map_candles(raw)
