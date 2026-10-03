"""Mapper: تبدیل پاسخ خام والکس به Entityهای دامنه.

تنها جایی که ساختار JSON والکس «می‌فهمد» همین فایل است.
"""

from decimal import Decimal, InvalidOperation
from typing import Any

from app.domain.entities.balance import Balance
from app.domain.entities.candle import Candle
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


def map_candles(raw_response: dict[str, Any]) -> list[Candle]:
    """تبدیل پاسخ UDF والکس به لیست Candle.

    ساختار پاسخ UDF:
        {
            "s": "ok",
            "t": [ts1, ts2, ...],
            "o": ["open1", "open2", ...],
            "h": [...],
            "l": [...],
            "c": [...],
            "v": [...]
        }
    """
    if raw_response.get("s") != "ok":
        return []

    times = raw_response.get("t", [])
    opens = raw_response.get("o", [])
    highs = raw_response.get("h", [])
    lows = raw_response.get("l", [])
    closes = raw_response.get("c", [])
    volumes = raw_response.get("v", [])

    n = len(times)
    if not (len(opens) == len(highs) == len(lows) == len(closes) == len(volumes) == n):
        raise ValueError("UDF response has mismatched array lengths")

    candles: list[Candle] = []
    for i in range(n):
        o = _dec(opens[i])
        h = _dec(highs[i])
        lo = _dec(lows[i])
        c = _dec(closes[i])
        v = _dec(volumes[i])
        if None in (o, h, lo, c, v):
            continue
        candles.append(
            Candle(
                time=int(times[i]),
                open=o,
                high=h,
                low=lo,
                close=c,
                volume=v,
            )
        )

    return candles


def _iso_to_ts(raw: Any) -> int:
    """تبدیل ISO 8601 string به Unix timestamp (ثانیه)."""
    if raw is None:
        return 0
    if isinstance(raw, (int, float)):
        return int(raw)
    if not isinstance(raw, str):
        return 0
    try:
        from datetime import datetime, timezone
        # پشتیبانی از فرمت "2026-10-03T20:13:41.000000Z"
        s = raw.replace("Z", "+00:00")
        dt = datetime.fromisoformat(s)
        return int(dt.timestamp())
    except (ValueError, TypeError):
        return 0


def map_order(raw: dict[str, Any]) -> "Order":
    """تبدیل پاسخ والکس به Order entity.

    Wallex از camelCase استفاده می‌کنه: clientOrderId, origQty, ...
    بعضی فیلدها ممکنه با underscore باشن: created_at, updated_at
    """
    from app.domain.entities.order import Order
    from app.domain.value_objects.order_enums import OrderSide, OrderStatus, OrderType

    # client_id: در پاسخ Wallex با "clientOrderId" میاد، در بعضی موارد "client_id"
    client_id = (
        raw.get("clientOrderId")
        or raw.get("client_id")
        or raw.get("clientId")
        or ""
    )

    # side: ممکنه خالی باشه
    side_raw = (raw.get("side") or "BUY").upper()
    try:
        side = OrderSide(side_raw)
    except ValueError:
        side = OrderSide.BUY

    # type
    type_raw = (raw.get("type") or "LIMIT").upper()
    try:
        order_type = OrderType(type_raw)
    except ValueError:
        order_type = OrderType.LIMIT

    # status
    status = OrderStatus.from_raw(raw.get("status"))

    return Order(
        client_id=str(client_id),
        symbol=raw.get("symbol", ""),
        side=side,
        type=order_type,
        status=status,
        price=_dec(raw.get("price")) or Decimal(0),
        stop_price=_dec(raw.get("stopPrice") or raw.get("stop_price")) or Decimal(0),
        orig_qty=_dec(raw.get("origQty")) or Decimal(0),
        executed_qty=_dec(raw.get("executedQty")) or Decimal(0),
        executed_price=_dec(raw.get("executedPrice")) or Decimal(0),
        executed_sum=_dec(raw.get("executedSum")) or Decimal(0),
        fee=_dec(raw.get("fee")) or Decimal(0),
        active=bool(raw.get("active", False)),
        executed_percent=_dec(raw.get("executedPercent")) or Decimal(0),
        created_at=_iso_to_ts(raw.get("created_at")),
        updated_at=_iso_to_ts(raw.get("updated_at")),
    )
