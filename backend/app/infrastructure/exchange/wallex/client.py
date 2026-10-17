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
from app.domain.entities.order import Order, OrderRequest
from app.domain.exceptions import (
    ExchangeAuthError,
    ExchangeError,
    ExchangeRateLimitError,
    ExchangeUnavailableError,
    InvalidSymbolError,
    OrderNotFoundError,
    OrderRejectedError,
)
from app.infrastructure.exchange.wallex.mapper import (
    map_balance,
    map_candles,
    map_market,
    map_order,
)


class WallexExchange:
    """Adapter صرافی والکس — پیاده‌ساز ExchangePort."""

    def __init__(self, settings: Settings, client: httpx.AsyncClient) -> None:
        self._settings = settings
        self._client = client
        self._log = structlog.get_logger("wallex.exchange")

    @classmethod
    def create(
        cls, settings: Settings, api_key: str | None = None
    ) -> WallexExchange:
        """ساخت با Connection Pool اختصاصی.

        Args:
            settings: تنظیمات سراسری
            api_key: توکن کاربر (phase 17.8). اگه None، از settings.WALLEX_API_KEY
                (توکن سراسری) استفاده می‌شه — برای endpointهای عمومی.
        """
        limits = httpx.Limits(
            max_connections=settings.WALLEX_MAX_CONNECTIONS,
            max_keepalive_connections=settings.WALLEX_MAX_CONNECTIONS // 2,
        )
        client = httpx.AsyncClient(
            base_url=settings.WALLEX_BASE_URL,
            headers={"x-api-key": api_key or settings.WALLEX_API_KEY},
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

    # ---------- Order operations ----------

    async def _post(self, path: str, json_body: dict[str, Any]) -> dict[str, Any]:
        """ارسال POST به والکس با مدیریت خطا."""
        try:
            r = await self._client.post(path, json=json_body)
        except httpx.TimeoutException as e:
            raise ExchangeUnavailableError(f"Timeout: POST {path}") from e
        except httpx.HTTPError as e:
            raise ExchangeUnavailableError(f"Network error: {e}") from e

        if r.status_code == 401:
            raise ExchangeAuthError("کلید API نامعتبر است")
        if r.status_code == 429:
            raise ExchangeRateLimitError("Rate Limit والکس")
        if r.status_code >= 500:
            raise ExchangeUnavailableError(f"Wallex {r.status_code}")
        if r.status_code >= 400:
            try:
                err_payload = r.json()
                msg = err_payload.get("message") or err_payload.get("error") or r.text[:200]
            except ValueError:
                msg = r.text[:200]
            raise OrderRejectedError(msg, code="order_rejected")

        try:
            payload = r.json()
        except ValueError as e:
            raise ExchangeError("پاسخ والکس JSON معتبر نیست") from e

        if not payload.get("success", True):
            msg = payload.get("message") or "Unknown error from Wallex"
            raise ExchangeError(msg, code="exchange_error")

        return payload

    async def place_order(self, request: OrderRequest) -> Order:
        """ثبت سفارش جدید در والکس.

        طبق مستندات: POST /v1/account/orders
        """
        body: dict[str, Any] = {
            "symbol": request.symbol,
            "side": request.side.value,
            "type": request.type.value,
            "quantity": str(request.quantity),
            "client_id": request.client_id,
        }
        if request.price is not None:
            body["price"] = str(request.price)
        if request.stop_price is not None:
            body["stop_Price"] = str(request.stop_price)
            body["stop_PriceCondition"] = request.stop_price_condition

        self._log.info(
            "placing_order",
            symbol=request.symbol,
            side=request.side.value,
            type=request.type.value,
            quantity=str(request.quantity),
            price=str(request.price) if request.price else None,
            stop_price=str(request.stop_price) if request.stop_price else None,
            stop_condition=request.stop_price_condition if request.stop_price else None,
            client_id=request.client_id,
        )

        payload = await self._post("/v1/account/orders", body)
        result = payload.get("result", {})
        order = map_order(result)

        self._log.info(
            "order_placed",
            client_id=order.client_id,
            status=order.status.value,
            active=order.active,
        )
        return order

    async def cancel_order(self, client_id: str, symbol: str) -> Order:
        """لغو سفارش با client_id.

        طبق مستندات: DELETE /v1/account/orders/{client_id}
        """
        self._log.info("canceling_order", client_id=client_id, symbol=symbol)

        try:
            r = await self._client.delete(
                f"/v1/account/orders/{client_id}",
                params={"symbol": symbol},
            )
        except httpx.TimeoutException as e:
            raise ExchangeUnavailableError(f"Timeout: cancel {client_id}") from e
        except httpx.HTTPError as e:
            raise ExchangeUnavailableError(f"Network error: {e}") from e

        if r.status_code == 401:
            raise ExchangeAuthError("کلید API نامعتبر است")
        if r.status_code == 404:
            raise OrderNotFoundError(f"سفارش {client_id} پیدا نشد")
        if r.status_code >= 500:
            raise ExchangeUnavailableError(f"Wallex {r.status_code}")
        if r.status_code >= 400:
            try:
                err_payload = r.json()
                msg = err_payload.get("message") or r.text[:200]
            except ValueError:
                msg = r.text[:200]
            raise ExchangeError(msg, code="cancel_failed")

        try:
            payload = r.json()
        except ValueError as e:
            raise ExchangeError("پاسخ والکس JSON معتبر نیست") from e

        if not payload.get("success", True):
            msg = payload.get("message") or "خطا در لغو سفارش"
            raise ExchangeError(msg, code="cancel_failed")

        result = payload.get("result", {})
        order = map_order(result)

        self._log.info(
            "order_canceled",
            client_id=order.client_id,
            status=order.status.value,
        )
        return order

    async def get_orders(
        self,
        symbol: str | None = None,
        status: str | None = None,
    ) -> list[Order]:
        """لیست سفارش‌های کاربر (read-only، برای تست).

        Args:
            symbol: فیلتر بر اساس نماد (مثلاً BTCTMN)
            status: فیلتر وضعیت (NEW, FILLED, CANCELED, ...)
        """
        params: dict[str, Any] = {}
        if symbol:
            params["symbol"] = symbol
        if status:
            params["status"] = status

        payload = await self._get("/v1/account/orders", **params)
        result = payload.get("result", {})

        # والکس ممکنه لیست یا dict برگردونه
        if isinstance(result, dict):
            orders_raw = result.get("orders") or result.get("items") or []
            if isinstance(orders_raw, dict):
                orders_raw = list(orders_raw.values())
        elif isinstance(result, list):
            orders_raw = result
        else:
            orders_raw = []

        return [map_order(o) for o in orders_raw if isinstance(o, dict)]

    async def get_open_orders(
        self,
        symbol: str | None = None,
        page: int = 1,
        per_page: int = 100,
    ) -> list[Order]:
        """دریافت سفارش‌های باز فعلی (شامل STOP_LIMIT و LIMIT).

        Args:
            symbol: فیلتر بر اساس نماد
            page: شماره صفحه (پیش‌فرض: ۱)
            per_page: تعداد در هر صفحه (پیش‌فرض: ۱۰۰)

        Returns:
            لیست سفارش‌های باز
        """
        params: dict[str, Any] = {"page": page, "per_page": per_page}
        if symbol:
            params["symbol"] = symbol

        payload = await self._get("/v1/account/openOrders", **params)
        result = payload.get("result", [])

        # result یه آرایه است
        if isinstance(result, list):
            orders_raw = result
        elif isinstance(result, dict):
            orders_raw = result.get("orders") or result.get("items") or []
        else:
            orders_raw = []

        return [map_order(o) for o in orders_raw if isinstance(o, dict)]
