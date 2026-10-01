"""Position Sizer — ML-based sizing.

ایده: به‌جای "همه یا هیچ"، بگه چند درصد سرمایه.

Target: بازده واقعی (نه باینری)
Features: RSI, ATR%, trend, regime, confidence

نتیجه: اگه بازده بالا → پوزیشن بزرگ
       اگه بازده کم  → پوزیشن کوچیک
"""

import asyncio
from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, r2_score

from app.application.use_cases.get_candles import GetCandlesUseCase
from app.core.config import get_settings
from app.domain.entities.candle import Candle
from app.infrastructure.exchange.wallex.client import WallexExchange
from app.services.indicators import atr, ema, rsi, volume_sma


@dataclass(slots=True)
class SizingResult:
    base_size_pct: float       # پایه (از قوانین)
    adjusted_size_pct: float   # با ML
    ml_prediction: float       # پیش‌بینی بازده
    confidence: float          # اطمینان (0-1)
    reason: str


def build_features(candles: list[Candle]) -> pd.DataFrame:
    """Features برای Position Sizing."""
    df = pd.DataFrame([
        {"time": c.time, "open": float(c.open), "high": float(c.high),
         "low": float(c.low), "close": float(c.close), "volume": float(c.volume)}
        for c in candles
    ])

    out = pd.DataFrame(index=df.index)

    # نوسان
    out["atr_pct"] = (df["high"] - df["low"]) / df["close"]

    # RSI
    delta = df["close"].diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()
    rs = gain / loss.replace(0, np.nan)
    out["rsi"] = 100 - (100 / (1 + rs))

    # MA ratios
    out["ma20_ratio"] = df["close"] / df["close"].rolling(20).mean() - 1
    out["ma50_ratio"] = df["close"] / df["close"].rolling(50).mean() - 1

    # Volume
    out["vol_ratio"] = df["volume"] / df["volume"].rolling(20).mean()

    # Momentum
    out["ret_5"] = df["close"].pct_change(5)
    out["ret_20"] = df["close"].pct_change(20)

    # Volatility
    out["volatility"] = df["close"].pct_change().rolling(20).std()

    return out


def build_target(candles: list[Candle], lookahead: int = 24) -> pd.Series:
    """Target: بازده واقعی در N کندل بعد."""
    df = pd.DataFrame([{"close": float(c.close)} for c in candles])
    future_ret = df["close"].shift(-lookahead) / df["close"] - 1
    return future_ret * 100  # درصد


async def fetch_all():
    SYMBOLS = ["BTCTMN", "ETHTMN", "XRPTMN", "DOGETMN", "SOLTMN"]
    settings = get_settings()

    async def one(sym):
        ex = WallexExchange.create(settings)
        try:
            uc = GetCandlesUseCase(exchange=ex)
            return sym, await uc.execute(symbol=sym, timeframe="15m", limit=2000)
        except Exception:
            return sym, []
        finally:
            await ex.aclose()

    results = await asyncio.gather(*[one(s) for s in SYMBOLS])
    return {s: c for s, c in results if c}


async def main():
    print("📥 دریافت داده...\n")
    markets_data = await fetch_all()

    train_X, train_y = [], []
    test_X, test_y = [], []

    for symbol, candles in markets_data.items():
        if len(candles) < 200:
            continue
        X = build_features(candles)
        y = build_target(candles)

        n = len(X)
        split = int(n * 0.6)
        train_X.append(X.iloc[:split])
        train_y.append(y.iloc[:split])
        test_X.append(X.iloc[split:])
        test_y.append(y.iloc[split:])
        print(f"  {symbol:10}  train={split:>5}  test={n-split:>5}")

    X_train = pd.concat(train_X, ignore_index=True)
    y_train = pd.concat(train_y, ignore_index=True)
    X_test = pd.concat(test_X, ignore_index=True)
    y_test = pd.concat(test_y, ignore_index=True)

    mask_tr = ~(X_train.isna().any(axis=1) | y_train.isna())
    mask_te = ~(X_test.isna().any(axis=1) | y_test.isna())
    X_train = X_train[mask_tr].reset_index(drop=True)
    y_train = y_train[mask_tr].reset_index(drop=True)
    X_test = X_test[mask_te].reset_index(drop=True)
    y_test = y_test[mask_te].reset_index(drop=True)

    print(f"\n📊 Train: {len(X_train)}  |  Test: {len(X_test)}")
    print(f"   Target mean: {y_train.mean():.3f}%")
    print(f"   Target std:  {y_train.std():.3f}%\n")

    # ---------- Gradient Boosting Regressor ----------
    print("🎓 آموزش Gradient Boosting Regressor...")
    model = GradientBoostingRegressor(
        n_estimators=100,
        max_depth=3,          # ← کم عمق، مقاوم
        learning_rate=0.05,
        min_samples_leaf=30,  # ← برگ بزرگ
        subsample=0.8,        # ← تصادفی برای جلوگیری از overfit
        random_state=42,
    )
    model.fit(X_train, y_train)

    # ارزیابی
    train_pred = model.predict(X_train)
    test_pred = model.predict(X_test)

    print(f"\n{'='*60}")
    print(f"📊 نتایج:")
    print(f"{'='*60}")
    print(f"  Train R²:  {r2_score(y_train, train_pred):.4f}")
    print(f"  Test R²:   {r2_score(y_test, test_pred):.4f}   ← معیار اصلی")
    print(f"  Train MAE: {mean_absolute_error(y_train, train_pred):.4f}%")
    print(f"  Test MAE:  {mean_absolute_error(y_test, test_pred):.4f}%")

    # توزیع پیش‌بینی‌ها در test
    print(f"\n📊 توزیع پیش‌بینی روی test:")
    percentiles = [10, 25, 50, 75, 90]
    for p in percentiles:
        val = np.percentile(test_pred, p)
        print(f"  {p:>2}%: {val:+.3f}%")

    # Feature importance
    imp = pd.Series(model.feature_importances_, index=X_train.columns).sort_values(ascending=False)
    print(f"\n🔍 Feature Importance:")
    for name, v in imp.items():
        bar = "█" * int(v * 50)
        print(f"  {name:15} {v:.4f}  {bar}")

    # ---------- تحلیل ارتباط ----------
    # آیا پیش‌بینی بالا = بازده بالا؟
    print(f"\n🎯 تحلیل: پیش‌بینی‌های بالا چقدر دقت دارن؟")
    print(f"{'─'*60}")

    # مرتب بر اساس پیش‌بینی
    idx_sorted = np.argsort(test_pred)[::-1]
    top_10_pct = int(len(idx_sorted) * 0.1)

    top_actual = y_test.iloc[idx_sorted[:top_10_pct]].mean()
    bottom_actual = y_test.iloc[idx_sorted[-top_10_pct:]].mean()
    overall_actual = y_test.mean()

    print(f"  میانگین همه:              {overall_actual:+.3f}%")
    print(f"  میانگین ۱۰٪ بهترین پیش‌بینی: {top_actual:+.3f}%  ← اگه بالا باشه، ML کار می‌کنه!")
    print(f"  میانگین ۱۰٪ بدترین پیش‌بینی: {bottom_actual:+.3f}%")

    spread = top_actual - bottom_actual
    print(f"\n  تفاوت بهترین و بدترین: {spread:+.3f}%")
    if spread > 0.5:
        print("  ✅ ML سیگنال داره!")
    elif spread > 0.2:
        print("  ⚠️ سیگنال ضعیف")
    else:
        print("  ❌ بدون سیگنال")


if __name__ == "__main__":
    asyncio.run(main())
