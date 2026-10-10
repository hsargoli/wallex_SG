"""Endpointهای تحلیل Nooaah."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.application.use_cases.analyze_symbol import AnalyzeSymbolUseCase
from app.infrastructure.analysis.factory import build_classifier
from app.presentation.api.deps import ExchangeDep

router = APIRouter(prefix="/analysis", tags=["analysis"])


class RegimeCounts(BaseModel):
    trending_up: int = 0
    trending_down: int = 0
    ranging: int = 0
    choppy: int = 0


class PersonalityOut(BaseModel):
    symbol: str
    timeframe: str
    window_count: int
    regime_counts: RegimeCounts
    dominant_regime: str | None
    volatility_mean: float
    volatility_std: float
    rsi_mean: float
    trend_mean: float


@router.get("/{symbol}", response_model=PersonalityOut)
async def analyze(
    symbol: str,
    exchange: ExchangeDep,
    timeframe: str = "1h",
) -> PersonalityOut:
    """تحلیل personality یه نماد."""
    uc = AnalyzeSymbolUseCase(exchange=exchange, classifier=build_classifier())
    stats = await uc.execute(symbol=symbol.upper(), timeframe=timeframe)
    counts = RegimeCounts(**{
        k: v for k, v in stats.regime_counts.items()
        if k in ("trending_up", "trending_down", "ranging", "choppy")
    })
    return PersonalityOut(
        symbol=stats.symbol,
        timeframe=stats.timeframe,
        window_count=stats.window_count,
        regime_counts=counts,
        dominant_regime=stats.dominant_regime,
        volatility_mean=stats.volatility_mean,
        volatility_std=stats.volatility_std,
        rsi_mean=stats.rsi_mean,
        trend_mean=stats.trend_mean,
    )
