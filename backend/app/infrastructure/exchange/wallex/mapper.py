"""Mapper: تبدیل پاسخ خام والکس به Entityهای دامنه.

تنها جایی که ساختار JSON والکس «می‌فهمد» همین فایل است.
"""

from decimal import Decimal, InvalidOperation
from typing import Any

from app.domain.entities.balance import Balance
from app.domain.entities.market import Market, TickerStats
from app.domain.value_objects.symbol import Symbol


def _dec(raw: Any) -> Decimal | None:
    if raw is None or raw == "":
        return None
    try:
        return Decimal(str(raw))
    except (InvalidOperation, ValueError):
        return None


def _int(raw: Any) -> int | None:
    if raw is None or raw == "":
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def map_ticker_stats(raw: dict[str, Any] | None) -> TickerStats | None:
    if not raw:
        return None
    direction = raw.get("direction") or {}
    return TickerStats(
        bid_price=_dec(raw.get("bidPrice")),
        ask_price=_dec(raw.get("askPrice")),
        last_price=_dec(raw.get("lastPrice")),
        last_quantity=_dec(raw.get("lastQty")),
        bid_volume=_dec(raw.get("bidVolume")),
        ask_volume=_dec(raw.get("askVolume")),
        daily_change_percent=_dec(raw.get("24h_ch")),
        weekly_change_percent=_dec(raw.get("7d_ch")),
        daily_volume=_dec(raw.get("24h_volume")),
        daily_quote_volume=_dec(raw.get("24h_quoteVolume")),
        daily_high=_dec(raw.get("24h_highPrice")),
        daily_low=_dec(raw.get("24h_lowPrice")),
        daily_trade_count=_int((direction.get("BUY") or 0) + (direction.get("SELL") or 0)) or None,
    )


def map_market(symbol_key: str, raw: dict[str, Any]) -> Market:
    return Market(
        symbol=Symbol(symbol_key),
        base_asset=raw.get("baseAsset", ""),
        quote_asset=raw.get("quoteAsset", ""),
        fa_name=raw.get("faName", ""),
        en_name=raw.get("enName", ""),
        base_precision=_int(raw.get("baseAssetPrecision")) or 0,
        quote_precision=_int(raw.get("quotePrecision")) or 0,
        min_quantity=_dec(raw.get("minQty")),
        min_notional=_dec(raw.get("minNotional")),
        step_size=_dec(raw.get("stepSize")),
        tick_size=_dec(raw.get("tickSize")),
        is_new=bool(raw.get("isNew", False)),
        is_zero_fee=bool(raw.get("isZeroFee", False)),
        stats=map_ticker_stats(raw.get("stats")),
    )


def map_balance(asset: str, raw: dict[str, Any]) -> Balance:
    # Wallex uses "value" for available balance
    raw_available = raw.get("value") if raw.get("value") is not None else raw.get("available")
    available = _dec(raw_available) or Decimal(0)
    locked = _dec(raw.get("locked")) or Decimal(0)
    return Balance(
        asset=asset.upper(),
        available=available,
        locked=locked,
        total=available + locked,
        fa_name=raw.get("faName"),
        en_name=raw.get("enName"),
    )


def map_order_book(raw_response: dict[str, Any], symbol: str) -> dict[str, Any]:
    """
    Maps Wallex depth raw response to internal OrderBook structure.
    """
    result = raw_response.get("result", {})
    raw_asks = result.get("ask", [])
    raw_bids = result.get("bid", [])

    asks = [
        {
            "price": Decimal(str(item["price"])),
            "quantity": Decimal(str(item["quantity"])),
            "sum": Decimal(str(item["sum"])) if item.get("sum") is not None else None,
        }
        for item in raw_asks[:20]
    ]

    bids = [
        {
            "price": Decimal(str(item["price"])),
            "quantity": Decimal(str(item["quantity"])),
            "sum": Decimal(str(item["sum"])) if item.get("sum") is not None else None,
        }
        for item in raw_bids[:20]
    ]

    best_ask = asks[0]["price"] if asks else None
    best_bid = bids[0]["price"] if bids else None

    spread = None
    spread_pct = None

    if best_ask is not None and best_bid is not None:
        spread = best_ask - best_bid
        if best_ask > 0:
            spread_pct = (spread / best_ask) * Decimal("100")

    return {
        "symbol": symbol,
        "best_bid": best_bid,
        "best_ask": best_ask,
        "spread": spread,
        "spread_pct": spread_pct,
        "bids": bids,
        "asks": asks,
    }
