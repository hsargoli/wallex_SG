"""AnalyzeSymbolUseCase — تحلیل «شخصیت» یه ارز در یه تایم‌فریم.

مراحل:
  ۱. کندل‌ها رو بگیر (از ExchangePort)
  ۲. feature استخراج کن برای هر پنجره
  ۳. regime تشخیص بده برای هر پنجره
  ۴. آمار جمع کن → PersonalityStats
"""

from __future__ import annotations

from collections import Counter
from typing import Sequence

from app.domain.analysis.entities.personality import PersonalityStats
from app.domain.analysis.entities.regime import RegimeResult
from app.domain.analysis.models.feature_math import extract_features
from app.domain.analysis.ports.regime_classifier import RegimeClassifierPort
from app.domain.entities.candle import Candle
from app.application.use_cases.get_candles import GetCandlesUseCase
from app.domain.ports.exchange import ExchangePort

WINDOW = 24       # پنجره‌ی feature extraction
CONTEXT = 200     # کندل‌های context به classifier (EMA100 نیاز داره)
MIN_CANDLES = 60


class AnalyzeSymbolUseCase:
    """تحلیل personality یه نماد در یه timeframe."""

    def __init__(
        self,
        exchange: ExchangePort,
        classifier: RegimeClassifierPort,
    ) -> None:
        self._exchange = exchange
        self._classifier = classifier
        self._get_candles = GetCandlesUseCase(exchange=exchange)

    async def execute(
        self,
        symbol: str,
        timeframe: str = "1h",
        limit: int = 500,
    ) -> PersonalityStats:
        candles = await self._get_candles.execute(
            symbol=symbol,
            timeframe=timeframe,
            limit=limit,
        )
        if not candles:
            return PersonalityStats(
                symbol=symbol,
                timeframe=timeframe,
                window_count=0,
            )
        return self._analyze(candles, symbol, timeframe)

    def _analyze(
        self,
        candles: Sequence[Candle],
        symbol: str,
        timeframe: str,
    ) -> PersonalityStats:
        if len(candles) < MIN_CANDLES:
            return PersonalityStats(
                symbol=symbol,
                timeframe=timeframe,
                window_count=0,
            )

        # Fit KMeans (اگه classifier KMeans باشه)
        if hasattr(self._classifier, "fit"):
            self._classifier.fit(candles)  # type: ignore[attr-defined]

        regime_counts: Counter[str] = Counter()
        vols: list[float] = []
        rsis: list[float] = []
        trends: list[float] = []
        window_count = 0

        for i in range(WINDOW, len(candles) + 1):
            feature_window = candles[i - WINDOW : i]
            context_window = candles[max(0, i - CONTEXT) : i]
            result: RegimeResult = self._classifier.classify(context_window)
            regime_counts[result.regime.value] += 1
            fv = extract_features(feature_window)
            vols.append(fv.volatility)
            rsis.append(fv.rsi)
            trends.append(fv.trend_strength)
            window_count += 1

        def _mean(xs: list[float]) -> float:
            return sum(xs) / len(xs) if xs else 0.0

        def _std(xs: list[float]) -> float:
            if len(xs) < 2:
                return 0.0
            m = _mean(xs)
            return (sum((x - m) ** 2 for x in xs) / len(xs)) ** 0.5

        return PersonalityStats(
            symbol=symbol,
            timeframe=timeframe,
            window_count=window_count,
            regime_counts=dict(regime_counts),
            volatility_mean=round(_mean(vols), 4),
            volatility_std=round(_std(vols), 4),
            rsi_mean=round(_mean(rsis), 2),
            trend_mean=round(_mean(trends), 4),
        )
