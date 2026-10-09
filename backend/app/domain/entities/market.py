"""Market و TickerStats — انتیتی‌های داده بازار."""

from dataclasses import dataclass
from decimal import Decimal

from app.domain.value_objects.symbol import Symbol


@dataclass(frozen=True, slots=True)
class TickerStats:
    """آماره‌های لحظه‌ای یک نماد."""

    bid_price: Decimal | None
    ask_price: Decimal | None
    last_price: Decimal | None
    last_quantity: Decimal | None
    bid_volume: Decimal | None
    ask_volume: Decimal | None
    daily_change_percent: Decimal | None
    weekly_change_percent: Decimal | None
    daily_volume: Decimal | None
    daily_quote_volume: Decimal | None
    daily_high: Decimal | None
    daily_low: Decimal | None
    daily_trade_count: int | None
    weekly_volume: Decimal | None = None
    bid_count: int | None = None
    ask_count: int | None = None


@dataclass(frozen=True, slots=True)
class Market:
    """یک مارکت/نماد معاملاتی در والکس."""

    symbol: Symbol
    base_asset: str
    quote_asset: str
    fa_name: str
    en_name: str
    base_precision: int
    quote_precision: int
    min_quantity: Decimal | None
    min_notional: Decimal | None
    step_size: Decimal | None
    tick_size: Decimal | None
    is_new: bool
    is_zero_fee: bool
    stats: TickerStats | None = None

    @property
    def last_price(self) -> Decimal | None:
        """آخرین قیمت معامله‌شده (از stats استخراج میشه)."""
        return self.stats.last_price if self.stats else None

    @property
    def bid_price(self) -> Decimal | None:
        return self.stats.bid_price if self.stats else None

    @property
    def ask_price(self) -> Decimal | None:
        return self.stats.ask_price if self.stats else None
