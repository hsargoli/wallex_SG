"""تحلیل صادقانه Overfitting.

مقایسه می‌کنیم:
  1. In-Sample (داده‌ای که مدل دیده) 
  2. Out-of-Sample (داده‌ای که ندیده)
"""

import asyncio
from datetime import datetime

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, roc_auc_score

from app.application.use_cases.get_candles import GetCandlesUseCase
from app.core.config import get_settings
from app.infrastructure.exchange.wallex.client import WallexExchange
from app.services.ml_bottom_model import build_features, candles_to_df


SYMBOLS = ["BTCTMN", "ETHTMN", "XRPTMN", "DOGETMN", "SOLTMN"]
TF = "15m"
LOOKAHEAD = 24
TP_PCT = 2.0
SL_PCT = 1.5


async def fetch(sym, start_ts, end_ts):
    settings = get_settings()
    ex = WallexExchange.create(settings)
    try:
        raw = await ex.get_candles(
            symbol=sym, resolution="15",
            from_ts=start_ts, to_ts=end_ts,
        )
        return sym, raw
    except Exception as e:
        print(f"  ❌ {sym}: {e}")
        return sym, []
    finally:
        await ex.aclose()


def build_label(df, lookahead=24, tp_pct=2.0, sl_pct=1.5):
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


def eval_period(X, y, name, model=None):
    mask = ~(X.isna().any(axis=1) | y.isna())
    X_c = X[mask].reset_index(drop=True)
    y_c = y[mask].reset_index(drop=True)

    if len(X_c) < 50 or y_c.nunique() < 2:
        print(f"  ⚠️ {name}: داده کم یا یک کلاس")
        return None

    if model is None:
        return None

    try:
        pred = model.predict(X_c)
        prob = model.predict_proba(X_c)[:, 1]
        acc = accuracy_score(y_c, pred)
        prec = precision_score(y_c, pred, zero_division=0)
        rec = recall_score(y_c, pred, zero_division=0)
        auc = roc_auc_score(y_c, prob)
        print(f"  {name:20}  n={len(X_c):>4}  Acc={acc:.3f}  Prec={prec:.3f}  Rec={rec:.3f}  AUC={auc:.4f}")
        return {"auc": auc, "acc": acc, "n": len(X_c)}
    except Exception as e:
        print(f"  ⚠️ {name}: {e}")
        return None


async def main():
    # دو دوره‌ی متفاوت
    periods = {
        "TRAIN (Sep 15-30)": (
            int(datetime(2026, 9, 15).timestamp()),
            int(datetime(2026, 9, 30).timestamp()),
        ),
        "TEST (Sep 1-14)": (
            int(datetime(2026, 9, 1).timestamp()),
            int(datetime(2026, 9, 14).timestamp()),
        ),
    }

    print("=" * 80)
    print("📊 تحلیل صادقانه Overfitting")
    print("=" * 80)

    # جمع‌آوری داده‌ی هر دو دوره
    data_by_period = {}
    for pname, (start, end) in periods.items():
        print(f"\n📥 {pname}...")
        X_parts, y_parts = [], []
        tasks = [fetch(s, start, end) for s in SYMBOLS]
        results = await asyncio.gather(*tasks)
        for sym, candles in results:
            if len(candles) < 100:
                continue
            df = candles_to_df(candles)
            X_parts.append(build_features(df))
            y_parts.append(build_label(df))
        X = pd.concat(X_parts, ignore_index=True) if X_parts else pd.DataFrame()
        y = pd.concat(y_parts, ignore_index=True) if y_parts else pd.Series()
        data_by_period[pname] = (X, y)
        print(f"  ✅ {len(X)} ردیف")

    # آموزش روی TRAIN
    print(f"\n🎓 آموزش مدل روی TRAIN...")
    X_train, y_train = data_by_period["TRAIN (Sep 15-30)"]
    mask = ~(X_train.isna().any(axis=1) | y_train.isna())
    X_tr = X_train[mask].reset_index(drop=True)
    y_tr = y_train[mask].reset_index(drop=True)

    model = RandomForestClassifier(
        n_estimators=300, max_depth=10, min_samples_leaf=10,
        random_state=42, n_jobs=-1,
    )
    model.fit(X_tr, y_tr)

    # ارزیابی
    print(f"\n{'='*80}")
    print("🎯 نتایج:")
    print(f"{'='*80}")
    print(f"  {'دوره':<22}  {'n':>5}  {'Acc':>6}  {'Prec':>6}  {'Rec':>6}  {'AUC':>7}")
    print(f"  {'-'*65}")

    in_sample = eval_period(X_tr, y_tr, "IN-SAMPLE (TRAIN)", model)
    X_test, y_test = data_by_period["TEST (Sep 1-14)"]
    out_sample = eval_period(X_test, y_test, "OUT-OF-SAMPLE (TEST)", model)

    if in_sample and out_sample:
        print(f"\n{'='*80}")
        print("📉 تفاوت عملکرد (Overfitting Detection):")
        print(f"{'='*80}")
        acc_gap = in_sample["acc"] - out_sample["acc"]
        auc_gap = in_sample["auc"] - out_sample["auc"]
        print(f"  تفاوت Accuracy:  {acc_gap:+.4f}")
        print(f"  تفاوت AUC:       {auc_gap:+.4f}")
        print()
        if auc_gap > 0.10:
            print("  🚨 OVERFITTING شدید! مدل فقط داده‌ی آموزش رو حفظ کرده")
        elif auc_gap > 0.05:
            print("  ⚠️ Overfitting متوسط")
        elif auc_gap > 0.02:
            print("  ⚠️ Overfitting خفیف")
        else:
            print("  ✅ مدل به خوبی generalize می‌کنه")


if __name__ == "__main__":
    asyncio.run(main())
