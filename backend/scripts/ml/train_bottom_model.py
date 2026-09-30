"""آموزش و ذخیره مدل ML روی 5 نماد 15m."""

import asyncio

from app.application.use_cases.get_candles import GetCandlesUseCase
from app.core.config import get_settings
from app.infrastructure.exchange.wallex.client import WallexExchange
from app.services.ml_bottom_model import (
    build_features,
    candles_to_df,
    save_model,
    train_model,
)


SYMBOLS = ["BTCTMN", "ETHTMN", "XRPTMN", "DOGETMN", "SOLTMN"]
TIMEFRAME = "15m"
N_CANDLES = 1000


async def fetch_one(sym: str):
    settings = get_settings()
    ex = WallexExchange.create(settings)
    try:
        uc = GetCandlesUseCase(exchange=ex)
        candles = await uc.execute(symbol=sym, timeframe=TIMEFRAME, limit=N_CANDLES)
        return sym, candles
    except Exception as e:
        print(f"  ❌ {sym}: {e}")
        return sym, []
    finally:
        await ex.aclose()


async def main():
    print(f"📥 دریافت {len(SYMBOLS)} نماد روی {TIMEFRAME}\n")

    tasks = [fetch_one(s) for s in SYMBOLS]
    results = await asyncio.gather(*tasks)

    markets_data = {}
    for sym, candles in results:
        if candles:
            markets_data[sym] = candles
            print(f"  ✅ {sym:10} {len(candles)} کندل")
        else:
            print(f"  ❌ {sym:10} خالی")

    if len(markets_data) < 2:
        print("\n❌ داده کافی نیست")
        return

    print(f"\n🎓 آموزش مدل روی {len(markets_data)} نماد...")
    model = train_model(markets_data)

    print("💾 ذخیره‌ی مدل...")
    path = save_model(model)
    print(f"✅ مدل ذخیره شد: {path}")

    # Feature importance
    import pandas as pd
    X_parts = []
    for candles in markets_data.values():
        df = candles_to_df(candles)
        if len(df) >= 100:
            X_parts.append(build_features(df))
    X = pd.concat(X_parts, ignore_index=True)
    imp = pd.Series(
        model.feature_importances_, index=X.columns
    ).sort_values(ascending=False)
    print("\n🔍 Top 10 features:")
    for name, v in imp.head(10).items():
        print(f"  {name:20} {v:.4f}")


if __name__ == "__main__":
    asyncio.run(main())
