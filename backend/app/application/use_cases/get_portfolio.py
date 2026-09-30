from dataclasses import dataclass
from decimal import Decimal

from app.domain.entities import Market
from app.domain.ports import ExchangePort


@dataclass(slots=True)
class PortfolioItem:
    asset: str
    fa_name: str | None
    available: Decimal
    locked: Decimal
    total: Decimal
    # قیمت‌های هر دو حالت
    price_usdt_bid: Decimal | None
    price_usdt_last: Decimal | None
    price_tmn_bid: Decimal | None
    price_tmn_last: Decimal | None
    # ارزش‌های هر دو حالت
    value_usdt_bid: Decimal | None
    value_usdt_last: Decimal | None
    value_tmn_bid: Decimal | None
    value_tmn_last: Decimal | None
    share_pct_bid: Decimal
    share_pct_last: Decimal
    has_tmn_pair: bool
    has_usdt_pair: bool


@dataclass(slots=True)
class Portfolio:
    total_value_tmn_bid: Decimal
    total_value_tmn_last: Decimal
    total_value_usdt_bid: Decimal
    total_value_usdt_last: Decimal
    usdt_tmn_rate: Decimal | None
    items: list[PortfolioItem]


class GetPortfolioUseCase:
    def __init__(self, exchange: ExchangePort) -> None:
        self.exchange = exchange

    @staticmethod
    def _price_bid(market: Market | None) -> Decimal | None:
        """قیمتی که اگه الان بفروشی می‌‌گیری (محافظه‌کارانه)."""
        if market is None:
            return None
        if market.bid_price and market.bid_price > 0:
            return market.bid_price
        return market.last_price or market.ask_price

    @staticmethod
    def _price_last(market: Market | None) -> Decimal | None:
        """آخرین قیمت معامله‌شده (ارزش اسمی)."""
        if market is None:
            return None
        return market.last_price or market.bid_price or market.ask_price

    async def execute(self) -> Portfolio:
        balances = await self.exchange.get_balances()
        markets = await self.exchange.get_markets()
        market_map: dict[str, Market] = {str(m.symbol).upper(): m for m in markets}

        usdt_tmn_market = (
            market_map.get("USDTTMN") or market_map.get("USDTIRT") or market_map.get("USDT_IRT")
        )
        usdt_tmn_rate = (
            usdt_tmn_market.last_price if usdt_tmn_market and usdt_tmn_market.last_price else None
        )

        items: list[PortfolioItem] = []

        for balance in balances:
            if balance.available <= 0:
                continue

            asset = balance.asset.upper()

            if asset in ("TMN", "IRT"):
                price_usdt_bid = (
                    Decimal(1) / usdt_tmn_rate if usdt_tmn_rate and usdt_tmn_rate > 0 else None
                )
                value_usdt_bid = (
                    balance.available / usdt_tmn_rate
                    if usdt_tmn_rate and usdt_tmn_rate > 0
                    else None
                )

                items.append(
                    PortfolioItem(
                        asset=asset,
                        fa_name=balance.fa_name,
                        available=balance.available,
                        locked=balance.locked,
                        total=balance.total,
                        price_usdt_bid=price_usdt_bid,
                        price_usdt_last=price_usdt_bid,
                        price_tmn_bid=Decimal(1),
                        price_tmn_last=Decimal(1),
                        value_usdt_bid=value_usdt_bid,
                        value_usdt_last=value_usdt_bid,
                        value_tmn_bid=balance.available,
                        value_tmn_last=balance.available,
                        share_pct_bid=Decimal(0),
                        share_pct_last=Decimal(0),
                        has_tmn_pair=True,
                        has_usdt_pair=False,
                    )
                )
                continue

            tmn_pair = market_map.get(f"{asset}TMN") or market_map.get(f"{asset}IRT")
            usdt_pair = market_map.get(f"{asset}USDT")

            price_tmn_bid = self._price_bid(tmn_pair)
            price_tmn_last = self._price_last(tmn_pair)

            price_usdt_bid = self._price_bid(usdt_pair)
            price_usdt_last = self._price_last(usdt_pair)

            # cross-rate محاسبات
            if price_tmn_bid is None and price_usdt_bid is not None and usdt_tmn_rate:
                price_tmn_bid = price_usdt_bid * usdt_tmn_rate
            if price_tmn_last is None and price_usdt_last is not None and usdt_tmn_rate:
                price_tmn_last = price_usdt_last * usdt_tmn_rate

            if (
                price_usdt_bid is None
                and price_tmn_bid is not None
                and usdt_tmn_rate
                and usdt_tmn_rate > 0
            ):
                price_usdt_bid = price_tmn_bid / usdt_tmn_rate
            if (
                price_usdt_last is None
                and price_tmn_last is not None
                and usdt_tmn_rate
                and usdt_tmn_rate > 0
            ):
                price_usdt_last = price_tmn_last / usdt_tmn_rate

            value_tmn_bid = balance.available * price_tmn_bid if price_tmn_bid else None
            value_tmn_last = balance.available * price_tmn_last if price_tmn_last else None

            value_usdt_bid = balance.available * price_usdt_bid if price_usdt_bid else None
            value_usdt_last = balance.available * price_usdt_last if price_usdt_last else None

            items.append(
                PortfolioItem(
                    asset=asset,
                    fa_name=balance.fa_name,
                    available=balance.available,
                    locked=balance.locked,
                    total=balance.total,
                    price_usdt_bid=price_usdt_bid,
                    price_usdt_last=price_usdt_last,
                    price_tmn_bid=price_tmn_bid,
                    price_tmn_last=price_tmn_last,
                    value_usdt_bid=value_usdt_bid,
                    value_usdt_last=value_usdt_last,
                    value_tmn_bid=value_tmn_bid,
                    value_tmn_last=value_tmn_last,
                    share_pct_bid=Decimal(0),
                    share_pct_last=Decimal(0),
                    has_tmn_pair=tmn_pair is not None,
                    has_usdt_pair=usdt_pair is not None,
                )
            )

        # جمع‌های کل
        total_tmn_bid = sum(
            (it.value_tmn_bid for it in items if it.value_tmn_bid is not None), Decimal(0)
        )
        total_tmn_last = sum(
            (it.value_tmn_last for it in items if it.value_tmn_last is not None), Decimal(0)
        )

        total_usdt_bid = sum(
            (it.value_usdt_bid for it in items if it.value_usdt_bid is not None), Decimal(0)
        )
        total_usdt_last = sum(
            (it.value_usdt_last for it in items if it.value_usdt_last is not None), Decimal(0)
        )

        if total_tmn_bid > 0:
            for it in items:
                if it.value_tmn_bid is not None:
                    it.share_pct_bid = (it.value_tmn_bid / total_tmn_bid) * Decimal(100)

        if total_tmn_last > 0:
            for it in items:
                if it.value_tmn_last is not None:
                    it.share_pct_last = (it.value_tmn_last / total_tmn_last) * Decimal(100)

        items.sort(key=lambda x: (x.value_tmn_bid is None, -(x.value_tmn_bid or Decimal(0))))

        return Portfolio(
            total_value_tmn_bid=total_tmn_bid,
            total_value_tmn_last=total_tmn_last,
            total_value_usdt_bid=total_usdt_bid,
            total_value_usdt_last=total_usdt_last,
            usdt_tmn_rate=usdt_tmn_rate,
            items=items,
        )
