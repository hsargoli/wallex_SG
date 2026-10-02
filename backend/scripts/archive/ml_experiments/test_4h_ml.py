"""تست ML روی 4h + رویکرد فیلتر.

سه تا رویکرد تست می‌کنیم:
  1. ML تنها (4h)
  2. قوانین تنها (4h)
  3. قوانین + ML به عنوان فیلتر
"""

import asyncio

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, roc_auc_score

from app.application.use_cases.get_candles import GetCandlesUseCase
from app.core.config import get_settings
from app.infrastructure.exchange.wallex.client import WallexExchange
from app.services.bottom_detector import detect_bottom
from app.services.ml_bottom_model import build_features, candles_to_df


SYMBOLS = ["BTCTMN", "ETHTMN", "XRPTMN", "DOGETMN", "SOLTMN"]
TF = "4h"
N_CANDLES = 300
LOOKAHEAD = 6       # 6 کندل 4h = 1 روز
TP_PCT = 3.0
SL_PCT = 2.0


async def fetch_all():
    settings = get_settings()
    async def one(sym):
        ex = WallexExchange.create(settings)
        try:
            uc = GetCandlesUseCase(exchange=ex)
            return sym, await uc.execute(symbol=sym, timeframe=TF, limit=N_CANDLES)
        except Exception as e:
            print(f"  ❌ {sym}: {e}")
            return sym, []
        finally:
            await ex.aclose()
    results = await asyncio.gather(*[one(s) for s in SYMBOLS])
    return {s: c for s, c in results if c}


def build_label(df, lookahead=6, tp_pct=3.0, sl_pct=2.0):
    labels = []
    for i in range(len(df)):
        if i + lookahead >= len(df):
            labels.append(np.nan)
            continue
        entry = df["close"].iloc[i]
        tp = entry * (1 + tp_pct / 100)
        sl = entry * (1 - sl_pct / 100)
        future = df.iloc[i + 1: i + lookahead + 1]
        hit_tp = hit_sl = None
        for j, (_, row) in enumerate(future.iterrows()):
            if hit_sl is None and row["low"] <= sl:
                hit_sl = j
            if hit_tp is None and row["high"] >= tp:
                hit_tp = j
            if hit_tp is not None or hit_sl is not None:
                break
        if hit_tp is not None and (hit_sl is None or hit_tp < hit_sl):
            labels.append(1)
        elif hit_sl is not None:
            labels.append(0)
        else:
            labels.append(np.nan)
    return pd.Series(labels, index=df.index)


async def main():
    print(f"📥 دریافت {len(SYMBOLS)} نماد × {TF}...\n")
    markets_data = await fetch_all()
    print(f"✅ {len(markets_data)} نماد\n")

    # جمع آوری داده
    train_X_parts, train_y_parts = [], []
    test_X_parts, test_y_parts = [], []
    test_symbols_data = []  # برای تحلیل رزولوشن

    for symbol, candles in markets_data.items():
        df = candles_to_df(candles)
        if len(df) < 150:
            continue
        X = build_features(df)
        y = build_label(df)
        n = len(X)
        split = int(n * 0.6)
        train_X_parts.append(X.iloc[:split])
        train_y_parts.append(y.iloc[:split])
        test_X_parts.append(X.iloc[split:])
        test_y_parts.append(y.iloc[split:])
        print(f"  {symbol:10}  total={n:>4}  train={split:>4}  test={n-split:>4}")

    X_train = pd.concat(train_X_parts, ignore_index=True)
    y_train = pd.concat(train_y_parts, ignore_index=True)
    X_test = pd.concat(test_X_parts, ignore_index=True)
    y_test = pd.concat(test_y_parts, ignore_index=True)

    mask_tr = ~(X_train.isna().any(axis=1) | y_train.isna())
    mask_te = ~(X_test.isna().any(axis=1) | y_test.isna())

    X_train = X_train[mask_tr].reset_index(drop=True)
    y_train = y_train[mask_tr].reset_index(drop=True)
    X_test = X_test[mask_te].reset_index(drop=True)
    y_test = y_test[mask_te].reset_index(drop=True)

    print(f"\n📊 Train: {len(X_train)} (pos: {y_train.mean()*100:.1f}%)")
    print(f"   Test:  {len(X_test)} (pos: {y_test.mean()*100:.1f}%)\n")

    # مدل
    print("🎓 آموزش مدل...")
    model = RandomForestClassifier(
        n_estimators=200, max_depth=5, min_samples_leaf=20,
        random_state=42, n_jobs=-1,
    )
    model.fit(X_train, y_train)

    # ارزیابی
    pred_te = model.predict(X_test)
    prob_te = model.predict_proba(X_test)[:, 1]

    print(f"\n{'='*70}")
    print(f"📊 نتایج 4h")
    print(f"{'='*70}")
    print(f"  Test Accuracy: {accuracy_score(y_test, pred_te):.4f}")
    try:
        auc = roc_auc_score(y_test, prob_te)
        print(f"  Test AUC:      {auc:.4f}")
    except ValueError:
        pass

    # توزیع احتمال — خیلی مهم
    print(f"\n📊 توزیع احتمال پیش‌بینی:")
    for low, high in [(0, 0.2), (0.2, 0.4), (0.4, 0.6), (0.6, 0.8), (0.8, 1.0)]:
        count = sum(1 for p in prob_te if low <= p < high)
        pct = count / len(prob_te) * 100
        bar = "█" * int(pct / 3)
        print(f"  [{low:.1f}-{high:.1f}]:  {count:>4}  {pct:>5.1f}%  {bar}")

    # تحلیل: احتمال بالا چقدر دقت داره؟
    print(f"\n🎯 Precision در سطوح مختلف آستانه:")
    for threshold in [0.5, 0.6, 0.7, 0.8]:
        mask = prob_te >= threshold
        if mask.sum() > 0:
            precision = y_test[mask].mean()
            print(f"  prob >= {threshold}:  n={mask.sum():>3}  precision={precision:.3f}")


if __name__ == "__main__":
    asyncio.run(main())
