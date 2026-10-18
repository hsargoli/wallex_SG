import logging
import httpx
import asyncio
from typing import Optional, List

from app.domain.ports.margin_exchange import (
    MarginExchangePort, MarginPosition, DryRunResult, OrderBookInfo,
    DryRunError, DryRunReason
)

logger = logging.getLogger(__name__)

_IDEMPOTENT_METHODS = {"GET", "HEAD", "OPTIONS"}
_REQUIRED_POSITION_FIELDS = {
    "id", "market", "side", "collateral",
    "open_price", "current_price", "liquidity_price",
}

class WallexMarginAdapter(MarginExchangePort):
    def __init__(self, api_key: str, base_url: str = "https://api.wallex.ir"):
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {
            "x-api-key": self.api_key,
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

    def __repr__(self):
        masked = f"{self.api_key[:4]}...{self.api_key[-4:]}" if len(self.api_key) > 8 else "***"
        return f"<WallexMarginAdapter base_url='{self.base_url}' api_key='{masked}'>"

    async def _request_with_retry(self, method: str, url: str, **kwargs) -> httpx.Response:
        max_retries = 3 if method.upper() in _IDEMPOTENT_METHODS else 1
        backoff = 1.0
        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient() as client:
                    resp = await client.request(method, url, **kwargs)
                    if resp.status_code in (429, 500, 502, 503, 504):
                        if attempt == max_retries - 1:
                            resp.raise_for_status()
                        await asyncio.sleep(backoff)
                        backoff *= 2
                        continue
                    return resp
            except httpx.RequestError as e:
                if attempt == max_retries - 1:
                    raise
                await asyncio.sleep(backoff)
                backoff *= 2
        return resp

    def _extract_result(self, response: httpx.Response) -> dict:
        response.raise_for_status()
        data = response.json()
        return data.get("result", data)

    def _parse_position(self, p: dict) -> MarginPosition:
        missing = _REQUIRED_POSITION_FIELDS - p.keys()
        if missing:
            raise ValueError(f"Wallex missing fields: {missing}. Keys: {list(p.keys())}")
        return MarginPosition(
            position_id=p["id"], market=p["market"], side=p["side"].lower(),
            collateral=float(p["collateral"]), entry_price=float(p["open_price"]),
            current_price=float(p["current_price"]), liquidation_price=float(p["liquidity_price"]),
            call_price=float(p["call_price"]) if p.get("call_price") else None,
            risk_coef=int(p.get("risk_coef", 1)), profit_percentage=float(p.get("profit_percentage", 0)),
            loan_amount=float(p.get("loan", 0)), interest=float(p.get("interest", 0)),
            stop_loss=float(p["stop_loss"]) if p.get("stop_loss") else None,
            take_profit=float(p["take_profit"]) if p.get("take_profit") else None,
            state=p.get("state", ""), extend_time=int(p.get("extend_time", 0))
        )

    async def get_balance(self) -> float:
        url = f"{self.base_url}/v1/account/balances"
        resp = await self._request_with_retry("GET", url, headers=self.headers)
        result = self._extract_result(resp)
        
        balances = result.get("balances", {})
        if isinstance(balances, dict):
            tmn = balances.get("TMN", {})
            return float(tmn.get("value", 0))
        return 0.0

    async def get_order_book(self, market: str) -> OrderBookInfo:
        url = f"{self.base_url}/v1/depth"
        resp = await self._request_with_retry("GET", url, params={"symbol": market}, headers=self.headers)
        result = self._extract_result(resp)
        
        bids = result.get("bid", [])
        asks = result.get("ask", [])
        best_bid = float(bids[0]["price"]) if bids else 0.0
        best_ask = float(asks[0]["price"]) if asks else 0.0
        mid = (best_bid + best_ask) / 2 if (best_bid + best_ask) > 0 else 0
        spread_pct = ((best_ask - best_bid) / mid * 100) if mid > 0 else 0
        
        return OrderBookInfo(spread_pct=spread_pct, best_bid=best_bid, best_ask=best_ask)

    async def dry_run(
        self, collateral: str, market: str, open_price: str, 
        risk_coef: str, side: str, stop_loss: Optional[str] = None, take_profit: Optional[str] = None
    ) -> DryRunResult:
        url = f"{self.base_url}/margin-trade/v1/public/dry-run"
        payload = {"collateral": collateral, "market": market, "open_price": open_price, "risk_coef": risk_coef, "side": side}
        if stop_loss: payload["stop_loss"] = stop_loss
        if take_profit: payload["take_profit"] = take_profit

        resp = await self._request_with_retry("POST", url, json=payload, headers=self.headers)
        
        if resp.status_code in (401, 403):
            raise DryRunError(DryRunReason.UNAUTHORIZED, f"HTTP {resp.status_code}")
        if resp.status_code == 400:
            try:
                err_msg = resp.json().get("message", "")
            except Exception:
                err_msg = resp.text[:200]
            if "ظرفیت" in err_msg:
                raise DryRunError(DryRunReason.NO_LIQUIDITY, err_msg)
            raise DryRunError(DryRunReason.INVALID_PAYLOAD, err_msg)
        if resp.status_code == 422:
            try:
                err_msg = resp.json().get("message", str(resp.json()))
            except Exception:
                err_msg = resp.text[:200]
            raise DryRunError(DryRunReason.INVALID_PAYLOAD, err_msg)
            
        result = self._extract_result(resp)
        return DryRunResult(
            liquidity_price=float(result.get("liquidity_price", 0)), call_price=float(result.get("call_price", 0)),
            open_fee=float(result.get("open_fee", 0)), trade_fee=float(result.get("trade_fee", 0)),
            extend_fee=float(result.get("extend_fee", 0)), loan_amount=float(result.get("loan", 0)),
            max_age=int(result.get("max_age", 0)), risk_coef=int(result.get("risk_coef", 1)),
            borrow_fee_pct_24h=float(result.get("borrow_fee_pct_24h", 0))
        )

    async def open_position(
        self, collateral: str, market: str, open_price: str, 
        risk_coef: str, side: str, stop_loss: Optional[str] = None, take_profit: Optional[str] = None
    ) -> MarginPosition:
        url = f"{self.base_url}/margin-trade/v1/positions"
        payload = {"collateral": collateral, "market": market, "open_price": open_price, "risk_coef": risk_coef, "side": side}
        if stop_loss: payload["stop_loss"] = stop_loss
        if take_profit: payload["take_profit"] = take_profit

        resp = await self._request_with_retry("POST", url, json=payload, headers=self.headers)
        result = self._extract_result(resp)
        return self._parse_position(result)

    async def get_positions(self, active: bool = True) -> List[MarginPosition]:
        url = f"{self.base_url}/margin-trade/v1/positions"
        resp = await self._request_with_retry("GET", url, params={"active": str(active).lower()}, headers=self.headers)
        result = self._extract_result(resp)
        if isinstance(result, list):
            return [self._parse_position(p) for p in result]
        return []

    async def close_position(self, position_id: str, price: str) -> MarginPosition:
        url = f"{self.base_url}/margin-trade/v1/positions/{position_id}/close"
        resp = await self._request_with_retry("PATCH", url, json={"price": price}, headers=self.headers)
        result = self._extract_result(resp)
        return self._parse_position(result)
