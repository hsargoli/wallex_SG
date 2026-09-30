"""Profitability analysis endpoints."""

from decimal import Decimal

from fastapi import APIRouter, HTTPException, status

from app.domain.models.profitability import (
    ProfitabilityRequest,
    ProfitabilityResponse,
)
from app.infrastructure.exchange.wallex.mapper import map_order_book
from app.presentation.api.deps import ExchangeDep
from app.services.profitability_service import profitability_service

router = APIRouter(prefix="/profitability", tags=["Profitability"])


def _as_dict(book) -> dict:
    """Normalize whatever map_order_book returns (dict or model) into a dict."""
    if isinstance(book, dict):
        return book
    return book.model_dump()


@router.post(
    "/evaluate",
    response_model=ProfitabilityResponse,
    status_code=status.HTTP_200_OK,
)
async def evaluate_profitability(
    payload: ProfitabilityRequest,
    exchange: ExchangeDep,
) -> ProfitabilityResponse:
    """ارزیابی سودآوری معامله با دفتر سفارش زنده."""
    try:
        raw_book = await exchange.get_order_book(symbol=payload.symbol)
        book = map_order_book(raw_book, symbol=payload.symbol)
        book_dict = _as_dict(book)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to fetch order book for {payload.symbol}: {e}",
        ) from e

    try:
        result = profitability_service.evaluate(
            request=payload,
            best_bid=Decimal(str(book_dict["best_bid"])),
            best_ask=Decimal(str(book_dict["best_ask"])),
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except KeyError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Order book missing required field: {e}",
        ) from e

    return result


@router.post(
    "/evaluate-with-snapshot",
    response_model=ProfitabilityResponse,
    status_code=status.HTTP_200_OK,
)
def evaluate_with_snapshot(
    payload: ProfitabilityRequest,
    best_bid: float,
    best_ask: float,
) -> ProfitabilityResponse:
    """ارزیابی سودآوری با قیمت‌های داده‌شده (بدون تماس با صرافی)."""
    try:
        result = profitability_service.evaluate(
            request=payload,
            best_bid=Decimal(str(best_bid)),
            best_ask=Decimal(str(best_ask)),
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    return result
