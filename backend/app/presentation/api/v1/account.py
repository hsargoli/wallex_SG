"""Endpointهای حساب کاربری."""

from decimal import Decimal

from fastapi import APIRouter, HTTPException
from app.domain.exceptions import ExchangeAuthError

from app.application.use_cases.get_balances import GetBalancesUseCase
from app.application.use_cases.get_cost_basis import GetCostBasisUseCase
from app.application.use_cases.get_portfolio import GetPortfolioUseCase
from app.presentation.api.deps import ExchangeDep
from app.presentation.api.v1.schemas import (
    BalanceOut,
    BalancesResponse,
    KeyBalancesResponse,
    PortfolioItemOut,
    PortfolioResponse,
    CostBasisItemOut,
    CostBasisResponse,
)

router = APIRouter(prefix="/account", tags=["account"])


@router.get("/balances", response_model=BalancesResponse)
async def get_balances(exchange: ExchangeDep) -> BalancesResponse:
    """موجودی همه دارایی‌های کاربر در والکس."""
    use_case = GetBalancesUseCase(exchange=exchange)
    balances = await use_case.execute()
    items = [BalanceOut.model_validate(b, from_attributes=True) for b in balances]
    return BalancesResponse(count=len(items), items=items)


@router.get("/key-assets", response_model=KeyBalancesResponse)
async def get_key_assets(exchange: ExchangeDep) -> KeyBalancesResponse:
    """دریافت لحظه‌ای دارایی‌های اصلی معاملاتی (TMN, USDT, XRP)."""
    use_case = GetBalancesUseCase(exchange=exchange)
    balances = await use_case.execute()
    balance_map = {b.asset.upper(): b for b in balances}

    tmn = balance_map.get("TMN") or balance_map.get("IRT")
    usdt = balance_map.get("USDT")
    xrp = balance_map.get("XRP")

    return KeyBalancesResponse(
        tmn_available=tmn.available if tmn else Decimal("0"),
        tmn_locked=tmn.locked if tmn else Decimal("0"),
        usdt_available=usdt.available if usdt else Decimal("0"),
        usdt_locked=usdt.locked if usdt else Decimal("0"),
        xrp_available=xrp.available if xrp else Decimal("0"),
        xrp_locked=xrp.locked if xrp else Decimal("0"),
    )


@router.get("/portfolio", response_model=PortfolioResponse)
async def get_portfolio(exchange: ExchangeDep) -> PortfolioResponse:
    """سبد دارایی با ارزش‌گذاری به تتر و تومان."""
    use_case = GetPortfolioUseCase(exchange=exchange)
    portfolio = await use_case.execute()

    items = [
        PortfolioItemOut(
            asset=it.asset,
            fa_name=it.fa_name,
            available=it.available,
            locked=it.locked,
            total=it.total,
            price_usdt_bid=it.price_usdt_bid,
            price_usdt_last=it.price_usdt_last,
            price_tmn_bid=it.price_tmn_bid,
            price_tmn_last=it.price_tmn_last,
            value_usdt_bid=it.value_usdt_bid,
            value_usdt_last=it.value_usdt_last,
            value_tmn_bid=it.value_tmn_bid,
            value_tmn_last=it.value_tmn_last,
            share_pct_bid=it.share_pct_bid,
            share_pct_last=it.share_pct_last,
            has_tmn_pair=it.has_tmn_pair,
            has_usdt_pair=it.has_usdt_pair,
        )
        for it in portfolio.items
    ]

    return PortfolioResponse(
        count=len(items),
        total_value_tmn_bid=portfolio.total_value_tmn_bid,
        total_value_tmn_last=portfolio.total_value_tmn_last,
        total_value_usdt_bid=portfolio.total_value_usdt_bid,
        total_value_usdt_last=portfolio.total_value_usdt_last,
        usdt_tmn_rate=portfolio.usdt_tmn_rate,
        items=items,
    )


@router.get("/cost-basis", response_model=CostBasisResponse)
async def get_cost_basis(exchange: ExchangeDep) -> CostBasisResponse:
    """میانگین وزنی قیمت خرید هر دارایی (BUY + FILLED)."""
    use_case = GetCostBasisUseCase(exchange=exchange)
    items = await use_case.execute()
    return CostBasisResponse(
        count=len(items),
        items=[
            CostBasisItemOut(
                symbol=it.symbol,
                avg_buy_price=it.avg_buy_price,
                total_qty_bought=it.total_qty_bought,
                total_invested=it.total_invested,
                orders_count=it.orders_count,
                buy_count=it.buy_count,
                sell_count=it.sell_count,
            )
            for it in items
        ],
    )
