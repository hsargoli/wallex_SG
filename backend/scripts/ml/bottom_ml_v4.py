"""ML v4 — 5 نماد × 3 تایم‌فریم."""

import asyncio

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import TimeSeriesSplit

from app.application.use_cases.get_candles import GetCandlesUseCase
from app.core.config import get_settings
from app.infrastructure.exchange.wallex.client import WallexExchange

SYMBOLS = ["BTCTMN", "ETHTMN", "XRPTMN", "DOGETMN", "SOLTMN"]
TIMEFRAMES = ["15m", "1h", "4h"]
N_CANDLES = 700
LOOKAHEAD = 24
TARGET_GAIN = 1.5
TARGET_LOSS = 1.0
RANDOM_STATE = 42


async def fetch_one(sym, tf):
    settings = get_settings()
    ex = WallexExchange.create(settings)
    try:
        uc = GetCandlesUseCase(exchange=ex)
        candles = await uc.execute(symbol=sym, timeframe=tf, limit=N_CANDLES)
        if not candles or len(candles) < 100:
            return None
        return pd.DataFrame([
            {"time": c.time, "open": float(c.open), "high": float(c.high),
             "low": float(c.low), "close": float(c.close), "volume": float(c.volume),
             "symbol": sym, "tf": tf}
            for c in candles
        ])
    except Exception:
        return None
    finally:
        await ex.aclose()


def rsi_series(close, period=14):
    delta = close.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = (-delta.clip(upper=0)).rolling(period).mean()
    rs = gain / loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def build_features(df):
    out = pd.DataFrame(index=df.index)
    out["rsi"] = rsi_series(df["close"], 14)
    out["rsi_lag1"] = out["rsi"].shift(1)
    out["rsi_lag3"] = out["rsi"].shift(3)
    out["rsi_change"] = out["rsi"] - out["rsi"].shift(1)
    out["ret_1"] = df["close"].pct_change(1)
    out["ret_3"] = df["close"].pct_change(3)
    out["ret_5"] = df["close"].pct_change(5)
    ma20 = df["close"].rolling(20).mean()
    ma50 = df["close"].rolling(50).mean()
    out["ma20_dist"] = (df["close"] - ma20) / ma20
    out["ma50_dist"] = (df["close"] - ma50) / ma50
    out["ma_cross"] = (ma20 - ma50) / ma50
    high20 = df["high"].rolling(20).max()
    low20 = df["low"].rolling(20).min()
    rng = (high20 - low20).replace(0, np.nan)
    out["pos_in_range"] = (df["close"] - low20) / rng
    out["near_low"] = (df["low"] - low20) / rng
    vol_ma = df["volume"].rolling(20).mean()
    out["vol_ratio"] = df["volume"] / vol_ma.replace(0, np.nan)
    out["vol_ma_ratio"] = vol_ma / df["volume"].rolling(50).mean()
    hl = df["high"] - df["low"]
    out["body_ratio"] = (df["close"] - df["open"]).abs() / hl.replace(0, np.nan)
    out["upper_wick"] = (df["high"] - df[["open", "close"]].max(axis=1)) / hl.replace(0, np.nan)
    out["lower_wick"] = (df[["open", "close"]].min(axis=1) - df["low"]) / hl.replace(0, np.nan)
    out["is_red"] = (df["close"] < df["open"]).astype(int)
    red = (df["close"] < df["open"]).astype(int)
    out["consec_red"] = red.groupby((red != red.shift()).cumsum()).cumsum()
    out["atr_pct"] = hl / df["close"]
    out["price_low_5"] = df["low"].rolling(5).min() / df["low"]
    out["rsi_low_5"] = out["rsi"].rolling(5).min()
    return out


def build_label(df):
    labels = []
    for i in range(len(df)):
        if i + LOOKAHEAD >= len(df):
            labels.append(np.nan)
            continue
        entry = df["close"].iloc[i]
        tp = entry * (1 + TARGET_GAIN / 100)
        sl = entry * (1 - TARGET_LOSS / 100)
        future = df.iloc[i + 1: i + LOOKAHEAD + 1]
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


def evaluate(X, y, name, verbose=True):
    mask = ~(X.isna().any(axis=1) | y.isna())
    X_clean = X[mask].reset_index(drop=True)
    y_clean = y[mask].reset_index(drop=True)

    if len(X_clean) < 100 or y_clean.nunique() < 2:
        return None

    tscv = TimeSeriesSplit(n_splits=5)
    all_y, all_pred, all_prob = [], [], []

    for tr, te in tscv.split(X_clean):
        X_tr, X_te = X_clean.iloc[tr], X_clean.iloc[te]
        y_tr, y_te = y_clean.iloc[tr], y_clean.iloc[te]
        if y_tr.nunique() < 2:
            continue
        model = RandomForestClassifier(
            n_estimators=200, max_depth=8, min_samples_leaf=10,
            class_weight="balanced", random_state=RANDOM_STATE, n_jobs=-1,
        )
        model.fit(X_tr, y_tr)
        all_y.extend(y_te.tolist())
        all_pred.extend(model.predict(X_te).tolist())
        all_prob.extend(model.predict_proba(X_te)[:, 1].tolist())

    if not all_y:
        return None

    auc = 0
    try:
        auc = roc_auc_score(all_y, all_prob)
    except ValueError:
        pass

    if verbose:
        print(f"  {name:20} n={len(X_clean):>5}  pos={int(y_clean.sum()):>5}  "
              f"Acc={accuracy_score(all_y, all_pred):.3f}  "
              f"Prec={precision_score(all_y, all_pred, zero_division=0):.3f}  "
              f"Rec={recall_score(all_y, all_pred, zero_division=0):.3f}  "
              f"AUC={auc:.4f}")

    return {"auc": auc, "n": len(X_clean), "name": name}


async def main():
    print(f"📥 دریافت {len(SYMBOLS)} نماد × {len(TIMEFRAMES)} تایم‌فریم\n")

    tasks = []
    for sym in SYMBOLS:
        for tf in TIMEFRAMES:
            tasks.append((sym, tf, fetch_one(sym, tf)))

    results = await asyncio.gather(*[t[2] for t in tasks])

    dfs = []
    for (sym, tf, _), df in zip(tasks, results):
        if df is not None:
            dfs.append(df)

    print(f"✅ {len(dfs)} دیتاست دریافت شد\n")
    print(f"{'='*80}")

    # ۱. ارزیابی هر TF جدا
    print("\n📊 ارزیابی جداگانه برای هر تایم‌فریم:")
    print(f"{'='*80}")

    for tf in TIMEFRAMES:
        tf_dfs = [d for d in dfs if d["tf"].iloc[0] == tf]
        if not tf_dfs:
            continue
        X_all = pd.concat([build_features(d) for d in tf_dfs], ignore_index=True)
        y_all = pd.concat([build_label(d) for d in tf_dfs], ignore_index=True)
        evaluate(X_all, y_all, f"TF={tf}")

    # ۲. ارزیابی ترکیبی همه TF ها
    print(f"\n{'='*80}")
    print("🎯 ترکیبی همه تایم‌فریم‌ها:")
    print(f"{'='*80}")

    X_all = pd.concat([build_features(d) for d in dfs], ignore_index=True)
    y_all = pd.concat([build_label(d) for d in dfs], ignore_index=True)
    result = evaluate(X_all, y_all, "همه ترکیبی")

    if result:
        auc = result["auc"]
        print()
        if auc >= 0.70:
            print("  🎉 عالی! قابل استفاده در production")
        elif auc >= 0.65:
            print("  ✅ خوب! قابل قبول")
        elif auc >= 0.60:
            print("  ⚠️  قابل قبول ولی می‌تونه بهتر بشه")
        else:
            print("  ❌ ضعیف")

        # Feature importance
        mask = ~(X_all.isna().any(axis=1) | y_all.isna())
        X_c = X_all[mask].reset_index(drop=True)
        y_c = y_all[mask].reset_index(drop=True)
        final = RandomForestClassifier(
            n_estimators=200, max_depth=8, min_samples_leaf=10,
            class_weight="balanced", random_state=RANDOM_STATE, n_jobs=-1,
        )
        final.fit(X_c, y_c)
        imp = pd.Series(final.feature_importances_, index=X_c.columns).sort_values(ascending=False)
        print("\n🔍 Top 10 features:")
        for name, v in imp.head(10).items():
            print(f"  {name:20} {v:.4f}")


if __name__ == "__main__":
    asyncio.run(main())
