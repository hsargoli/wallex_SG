"""LGBMClassifier — پیاده‌سازی RegimeClassifierPort با LightGBM.

مدل از data/models/nooaah_lgbm_v1.txt لود می‌شه.
اگه نبود → fallback به RuleBasedClassifier.
"""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

import lightgbm as lgb
import numpy as np
import pandas as pd

from app.domain.analysis.entities.regime import RegimeResult, RegimeType
from app.domain.entities.candle import Candle
from app.infrastructure.analysis.rule_based_classifier import RuleBasedClassifier
from app.services.ml_bottom_model import build_features, candles_to_df

MODEL_PATH = Path("data/models/nooaah_lgbm_v1.txt")
PROB_THRESHOLD = 0.60  # آستانه‌ی trending_up
MIN_CANDLES = 120  # برای محاسبه‌ی feature ها


class LGBMClassifier:
    """طبقه‌بندی regime با LightGBM (binary: trending_up vs not)."""

    def __init__(self, model_path: Path | None = None) -> None:
        self._path = model_path or MODEL_PATH
        self._model: lgb.Booster | None = None
        self._fallback = RuleBasedClassifier()
        self._load()

    def _load(self) -> None:
        if self._path.exists():
            try:
                self._model = lgb.Booster(model_file=str(self._path))
            except Exception:
                self._model = None

    @property
    def has_model(self) -> bool:
        return self._model is not None

    def classify(self, candles: Sequence[Candle]) -> RegimeResult:
        if len(candles) < MIN_CANDLES:
            return RegimeResult(
                regime=RegimeType.RANGING,
                confidence=0,
                reasons=("داده کافی نیست",),
                is_tradeable=False,
            )

        if self._model is None:
            # fallback
            return self._fallback.classify(candles)

        try:
            df = candles_to_df(list(candles))
            X = build_features(df)
            # آخرین ردیف (کندل فعلی)
            last = X.iloc[[-1]]
            if last.isna().any(axis=1).iloc[0]:
                # feature ناقص → fallback
                return self._fallback.classify(candles)

            prob = float(self._model.predict(last)[0])
        except Exception:
            return self._fallback.classify(candles)

        confidence = int(round(prob * 100))

        if prob >= PROB_THRESHOLD:
            regime = RegimeType.TRENDING_UP
            is_tradeable = True
        elif prob >= 0.4:
            regime = RegimeType.CHOPPY
            is_tradeable = False
        else:
            regime = RegimeType.RANGING
            is_tradeable = False

        return RegimeResult(
            regime=regime,
            confidence=confidence,
            reasons=(
                f"LGBM prob={prob:.3f}",
                f"threshold={PROB_THRESHOLD}",
            ),
            is_tradeable=is_tradeable,
        )
