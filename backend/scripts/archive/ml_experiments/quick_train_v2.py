"""اسکریپت v2: داده بیشتر + Feature بهتر + چند Target.

تغییرات نسبت به v1:
- دریافت داده‌ی بیشتر از Wallex (مستقیم، بدون limit)
- ~30 feature (lag features + trend + الگو)
- تست چند Target مختلف
"""

import asyncio
import time

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from sklearn.model_selection import TimeSeriesSplit

from app.core.config import get_settings
from app.infrastructure.exchange.wallex.client import WallexExchange

# ---------- تنظیمات ----------
SYMBOL = "BTCTMN"
RESOLUTION = "60"           # 60 = 1 ساعت
DAYS_BACK = 120             # تلاش برای ۱۲۰ روز
RANDOM_STATE = 42


# ---------- ۱. دریافت داده ----------
async def fetch_candles() -> pd.DataFrame:
    """دریافت کندل مستقیم از Wallex بدون محدودیت."""
    settings = get_settings()
    ex = WallexExchange.create(settings)
    try:
        now = int(time.time())
        from_ts = now - DAYS_BACK * 86400
        candles = await ex.get_candles(
            symbol=SYMBOL,
            resolution=RESOLUTION,
            from_ts=from_ts,
            to_ts=now,
        )
    finally:
        await ex.aclose()

    df = pd.DataFrame(
        [
            {
                "time": c.time,
                "open": float(c.open),
                "high": float(c.high),
                "low": float(c.low),
                "close": float(c.close),
                "volume": float(c.volume),
            }
            for c in candles
        ]
    )
    return df


# ---------- ۲. Features (گسترده) ----------
def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """ساخت ~30 feature."""
    out = pd.DataFrame(index=df.index)

    # ========== بازده ==========
    out["return_1"] = df["close"].pct_change(1)
    out["return_3"] = df["close"].pct_change(3)
    out["return_5"] = df["close"].pct_change(5)
    out["return_1_lag1"] = out["return_1"].shift(1)
    out["return_1_lag3"] = out["return_1"].shift(3)

    # ========== MA / EMA ==========
    ma20 = df["close"].rolling(20).mean()
    ma50 = df["close"].rolling(50).mean()
    out["ma_20_ratio"] = df["close"] / ma20 - 1.0
    out["ma_50_ratio"] = df["close"] / ma50 - 1.0

    ema9 = df["close"].ewm(span=9, adjust=False).mean()
    ema21 = df["close"].ewm(span=21, adjust=False).mean()
    out["ema_9_21_diff"] = (ema9 - ema21) / df["close"]

    # ========== موقعیت قیمت ==========
    high20 = df["high"].rolling(20).max()
    low20 = df["low"].rolling(20).min()
    range20 = (high20 - low20).replace(0, np.nan)
    out["price_position_20"] = (df["close"] - low20) / range20

    # ========== حجم ==========
    vol_ma20 = df["volume"].rolling(20).mean()
    out["volume_ratio"] = df["volume"] / vol_ma20.replace(0, np.nan)
    out["volume_ratio_lag3"] = out["volume_ratio"].shift(3)
    out["volume_trend"] = (
        df["volume"].rolling(5).mean() / df["volume"].rolling(20).mean()
    ) - 1.0

    # ========== شکل کندل ==========
    hl_range = df["high"] - df["low"]
    body = (df["close"] - df["open"]).abs()
    out["hl_range"] = hl_range / df["close"]
    out["body_ratio"] = body / hl_range.replace(0, np.nan)
    out["upper_wick_ratio"] = (
        df["high"] - df[["open", "close"]].max(axis=1)
    ) / hl_range.replace(0, np.nan)
    out["lower_wick_ratio"] = (
        df[["open", "close"]].min(axis=1) - df["low"]
    ) / hl_range.replace(0, np.nan)
    out["candle_direction"] = (df["close"] > df["open"]).astype(int)

    # ========== RSI ==========
    delta = df["close"].diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()
    rs = gain / loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    out["rsi_14"] = rsi
    out["rsi_lag1"] = rsi.shift(1)
    out["rsi_lag3"] = rsi.shift(3)
    out["rsi_change"] = rsi - rsi.shift(1)

    # ========== نوسان ==========
    out["volatility_5"] = df["close"].pct_change().rolling(5).std()
    out["volatility_20"] = df["close"].pct_change().rolling(20).std()

    # ========== زمان ==========
    dt = pd.to_datetime(df["time"], unit="s", utc=True)
    out["hour_of_day"] = dt.dt.hour
    out["day_of_week"] = dt.dt.dayofweek

    return out


# ---------- ۳. Labels مختلف ----------
def build_label_direction(df: pd.DataFrame, n: int) -> pd.Series:
    """جهت در n کندل بعد: 1=صعودی."""
    return (df["close"].shift(-n) > df["close"]).astype(int)


def build_label_threshold(df: pd.DataFrame, n: int, threshold: float) -> pd.Series:
    """آیا بازده در n کندل بعد از threshold بیشتره؟ 1=بله."""
    future_return = df["close"].shift(-n) / df["close"] - 1.0
    return (future_return > threshold).astype(int)


# ---------- ۴. آموزش و ارزیابی ----------
def evaluate(X: pd.DataFrame, y: pd.Series, name: str) -> float:
    """آموزش و ارزیابی. برمی‌گردونه دقت میانگین."""
    mask = ~(X.isna().any(axis=1) | y.isna())
    X_clean = X[mask].reset_index(drop=True)
    y_clean = y[mask].reset_index(drop=True)

    if len(X_clean) < 100:
        print(f"⚠️  {name}: داده کافی نیست ({len(X_clean)})")
        return 0.0

    # چک کن دو کلاس داریم
    if y_clean.nunique() < 2:
        print(f"⚠️  {name}: فقط یک کلاس (class imbalance شدید)")
        return 0.0

    tscv = TimeSeriesSplit(n_splits=5)
    fold_accuracies: list[float] = []

    for train_idx, test_idx in tscv.split(X_clean):
        X_train = X_clean.iloc[train_idx]
        X_test = X_clean.iloc[test_idx]
        y_train = y_clean.iloc[train_idx]
        y_test = y_clean.iloc[test_idx]

        # چک کن هر دو کلاس توی train هستن
        if y_train.nunique() < 2:
            continue

        model = RandomForestClassifier(
            n_estimators=150,
            max_depth=10,
            min_samples_leaf=15,
            random_state=RANDOM_STATE,
            n_jobs=-1,
        )
        model.fit(X_train, y_train)
        acc = accuracy_score(y_test, model.predict(X_test))
        fold_accuracies.append(acc)

    if not fold_accuracies:
        return 0.0

    mean_acc = float(np.mean(fold_accuracies))
    baseline = float(y_clean.mean())
    print(
        f"{name:30} acc={mean_acc:.4f}  baseline={baseline:.4f}  "
        f"improvement={(mean_acc - baseline)*100:+.2f}%  n={len(X_clean)}"
    )
    return mean_acc


# ---------- main ----------
async def main() -> None:
    print(f"📥 دریافت کندل {SYMBOL}...")
    df = await fetch_candles()
    print(f"✅ {len(df)} کندل دریافت شد")

    if len(df) < 100:
        print("❌ داده کافی نیست")
        return

    print(f"   از {pd.to_datetime(df['time'].iloc[0], unit='s')}")
    print(f"   تا {pd.to_datetime(df['time'].iloc[-1], unit='s')}")

    print("\n🔧 ساخت Features...")
    X = build_features(df)
    print(f"✅ {X.shape[1]} feature")

    print("\n🚀 تست چند Target:\n")

    # جهت‌ها
    for n in [1, 2, 3, 4, 5]:
        y = build_label_direction(df, n)
        evaluate(X, y, f"direction_{n}")

    print()
    # Threshold ها
    for n, th in [(4, 0.003), (4, 0.005), (4, 0.01), (6, 0.01)]:
        y = build_label_threshold(df, n, th)
        evaluate(X, y, f"return_{n} > {th*100:.1f}%")


if __name__ == "__main__":
    asyncio.run(main())
