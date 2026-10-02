"""ML v6 — Label سخت‌تر (TP=3%, SL=1.5%)."""

import asyncio

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import TimeSeriesSplit

from app.application.use_cases.get_candles import GetCandlesUseCase
from app.core.config import get_settings
from app.infrastructure.exchange.wallex.client import WallexExchange
from app.services.ml_bottom_model import build_features, candles_to_df, save_model

SYMBOLS = ["BTCTMN", "ETHTMN", "XRPTMN", "DOGETMN", "SOLTMN"]
TIMEFRAME = "15m"
N_CANDLES = 1000
LOOKAHEAD = 24
TARGET_GAIN = 3.0      # ← سخت‌تر
TARGET_LOSS = 1.5      # ← متعادل‌تر
RANDOM_STATE = 42


async def fetch_one(sym):
    settings = get_settings()
    ex = WallexExchange.create(settings)
    try:
        uc = GetCandlesUseCase(exchange=ex)
        candles = await uc.execute(symbol=sym, timeframe=TIMEFRAME, limit=N_CANDLES)
        return sym, candles
    except Exception:
        return sym, []
    finally:
        await ex.aclose()


def build_label_strict(df, lookahead=24, tp_pct=3.0, sl_pct=1.5):
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
    print(f"📥 دریافت {len(SYMBOLS)} نماد روی {TIMEFRAME}\n")

    tasks = [fetch_one(s) for s in SYMBOLS]
    results = await asyncio.gather(*tasks)

    X_parts, y_parts = [], []
    for sym, candles in results:
        if not candles or len(candles) < 100:
            print(f"  ❌ {sym}")
            continue
        df = candles_to_df(candles)
        X_parts.append(build_features(df))
        y_parts.append(build_label_strict(df))
        print(f"  ✅ {sym:10} {len(candles)} کندل")

    X = pd.concat(X_parts, ignore_index=True)
    y = pd.concat(y_parts, ignore_index=True)
    mask = ~(X.isna().any(axis=1) | y.isna())
    X_c = X[mask].reset_index(drop=True)
    y_c = y[mask].reset_index(drop=True)

    print(f"\n📊 توزیع Label (TP={TARGET_GAIN}%, SL={TARGET_LOSS}%):")
    print(f"   مثبت (کف واقعی): {int(y_c.sum())}")
    print(f"   منفی:             {int(len(y_c) - y_c.sum())}")
    print(f"   نرخ کف:           {y_c.mean()*100:.1f}%\n")

    if y_c.mean() > 0.35:
        print("⚠️ هنوز نرخ کف بالاست. سخت‌ترش کن.")
        return

    # آموزش
    print("🎓 آموزش RandomForest...")
    tscv = TimeSeriesSplit(n_splits=5)
    all_y, all_pred, all_prob = [], [], []

    for tr, te in tscv.split(X_c):
        X_tr, X_te = X_c.iloc[tr], X_c.iloc[te]
        y_tr, y_te = y_c.iloc[tr], y_c.iloc[te]
        if y_tr.nunique() < 2:
            continue
        model = RandomForestClassifier(
            n_estimators=300, max_depth=10, min_samples_leaf=10,
            random_state=RANDOM_STATE, n_jobs=-1,
        )
        model.fit(X_tr, y_tr)
        all_y.extend(y_te.tolist())
        all_pred.extend(model.predict(X_te).tolist())
        all_prob.extend(model.predict_proba(X_te)[:, 1].tolist())

    print(f"\n{'='*70}")
    print(f"🎯 نتیجه v6")
    print(f"{'='*70}")
    print(f"  Accuracy:   {accuracy_score(all_y, all_pred):.4f}")
    print(f"  Precision:  {precision_score(all_y, all_pred, zero_division=0):.4f}")
    print(f"  Recall:     {recall_score(all_y, all_pred, zero_division=0):.4f}")
    try:
        auc = roc_auc_score(all_y, all_prob)
        print(f"  AUC-ROC:    {auc:.4f}")
        if auc >= 0.70:
            print("  🎉 عالی!")
        elif auc >= 0.65:
            print("  ✅ خوب")
        elif auc >= 0.60:
            print("  ⚠️ قابل قبول")
        else:
            print("  ❌ ضعیف")
    except ValueError:
        print("  ❌ AUC محاسبه نشد")

    # توزیع احتمال
    print(f"\n📊 توزیع احتمال ML:")
    bins = [0, 0.2, 0.4, 0.6, 0.8, 1.0]
    for i in range(len(bins)-1):
        count = sum(1 for p in all_prob if bins[i] <= p < bins[i+1])
        pct = count / len(all_prob) * 100
        bar = "█" * int(pct / 2)
        print(f"  [{bins[i]:.1f}-{bins[i+1]:.1f}]: {count:>5}  {pct:>5.1f}%  {bar}")

    # آموزش نهایی و ذخیره
    print("\n💾 آموزش نهایی + ذخیره...")
    final = RandomForestClassifier(
        n_estimators=300, max_depth=10, min_samples_leaf=10,
        random_state=RANDOM_STATE, n_jobs=-1,
    )
    final.fit(X_c, y_c)
    path = save_model(final)
    print(f"✅ ذخیره شد: {path}")


if __name__ == "__main__":
    asyncio.run(main())
