"""KMeansClassifier — پیاده‌سازی RegimeClassifierPort با sklearn.

روی featureهای پنجره‌های لغزان KMeans می‌زنه، K رو با silhouette
انتخاب می‌کنه، و به هر خوشه یه برچسب انسانی (RegimeType) می‌چسبونه.

نکته: sklearn KMeans با n_init='auto' داخلی k-means++ داره —
پس نیازی به پیاده‌سازی دستی نیست.
"""

from __future__ import annotations

from typing import Sequence

import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

from app.domain.analysis.entities.regime import RegimeResult, RegimeType
from app.domain.analysis.models.feature_math import extract_features
from app.domain.entities.candle import Candle

WINDOW = 24
STEP = 1
MIN_WINDOWS = 30


class KMeansClassifier:
    """KMeans-based regime classifier (sklearn)."""

    def __init__(self, k_min: int = 2, k_max: int = 6, seed: int = 42) -> None:
        self._k_min = k_min
        self._k_max = k_max
        self._seed = seed
        self._scaler: StandardScaler | None = None
        self._model: KMeans | None = None
        self._labels: dict[int, RegimeType] = {}
        self._k: int = 0

    def fit(self, candles: Sequence[Candle]) -> None:
        """آموزش روی featureهای پنجره‌های لغزان."""
        if len(candles) < WINDOW + MIN_WINDOWS:
            self._model = None
            return

        rows: list[tuple[float, float, float, float]] = []
        for i in range(WINDOW, len(candles) + 1, STEP):
            fv = extract_features(candles[i - WINDOW : i])
            rows.append(fv.as_tuple())

        X = np.asarray(rows, dtype=float)
        scaler = StandardScaler().fit(X)
        Xs = scaler.transform(X)

        best_k, best_score, best_model = 0, -2.0, None
        for k in range(self._k_min, self._k_max + 1):
            if len(Xs) < k * 2:
                break
            model = KMeans(
                n_clusters=k, n_init="auto", random_state=self._seed
            ).fit(Xs)
            score = float(silhouette_score(Xs, model.labels_))
            if score > best_score:
                best_k, best_score, best_model = k, score, model

        if best_model is None:
            self._model = None
            return

        self._scaler = scaler
        self._model = best_model
        self._k = best_k
        self._labels = self._label_clusters(X, best_model.labels_, best_k)

    def _label_clusters(
        self, X_raw: np.ndarray, labels: np.ndarray, k: int
    ) -> dict[int, RegimeType]:
        """برچسب انسانی به هر خوشه بر اساس percentileهای داده.

        آستانه‌ها نسبی هستن (نه ثابت) — چون مقیاس volatility
        در ارزهای مختلف متفاوته.

        X_raw: (n, 4) — [volatility, rsi, trend_strength, volume_z]
        """
        all_vols = X_raw[:, 0]
        all_trends = X_raw[:, 2]
        vol_p33, vol_p66 = np.percentile(all_vols, [33, 66])
        trend_p33, trend_p66 = np.percentile(all_trends, [33, 66])

        out: dict[int, RegimeType] = {}
        for cid in range(k):
            mask = labels == cid
            if not mask.any():
                out[cid] = RegimeType.RANGING
                continue
            vol_mean = float(X_raw[mask, 0].mean())
            trend_mean = float(X_raw[mask, 2].mean())

            # اولویت: trend قوی (بالاتر از p66) قبل از vol
            if trend_mean >= trend_p66 and trend_mean > 0:
                out[cid] = RegimeType.TRENDING_UP
            elif trend_mean <= trend_p33 and trend_mean < 0:
                out[cid] = RegimeType.TRENDING_DOWN
            elif vol_mean >= vol_p66:
                out[cid] = RegimeType.CHOPPY
            else:
                out[cid] = RegimeType.RANGING
        return out

    def classify(self, candles: Sequence[Candle]) -> RegimeResult:
        """regime کندل آخر رو تشخیص بده."""
        if self._model is None or self._scaler is None or len(candles) < WINDOW:
            return RegimeResult(
                regime=RegimeType.RANGING,
                confidence=0,
                reasons=("مدل آموزش ندیده یا داده کم",),
                is_tradeable=False,
            )

        fv = extract_features(candles[-WINDOW:])
        x = np.asarray([fv.as_tuple()], dtype=float)
        xs = self._scaler.transform(x)
        cid = int(self._model.predict(xs)[0])
        label = self._labels.get(cid, RegimeType.RANGING)

        is_tradeable = label in (RegimeType.TRENDING_UP, RegimeType.RANGING)
        return RegimeResult(
            regime=label,
            confidence=65,
            reasons=(
                f"KMeans K={self._k}",
                f"خوشه {cid}",
                f"vol={fv.volatility:.2f} trend={fv.trend_strength:.1f}",
            ),
            is_tradeable=is_tradeable,
        )
