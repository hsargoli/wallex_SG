"""دیباگ trend_follow — چرا fire نمی‌کنه؟"""
import asyncio
from collections import Counter

from app.application.use_cases.get_candles import GetCandlesUseCase
from app.core.config import get_settings
from app.infrastructure.exchange.wallex.client import WallexExchange
from app.services.regime_detector import detect_regime
from app.services.bots.trend_follow.config import TrendFollowConfig
from app.services.bots.trend_follow.strategy import evaluate_entry

SYMBOLS = ["XRPTMN", "ZECTMN", "SOLTMN", "BTCTMN"]
TF = "1h"
N = 2000


async def fetch_one(sym, settings):
    ex = WallexExchange.create(settings)
    try:
        uc = GetCandlesUseCase(exchange=ex)
        return sym, await uc.execute(symbol=sym, timeframe=TF, limit=N)
    finally:
        await ex.aclose()


async def main():
    settings = get_settings()
    cfg = TrendFollowConfig()
    results = await asyncio.gather(*[fetch_one(s, settings) for s in SYMBOLS])

    for sym, candles in results:
        if not candles:
            continue

        print(f"\n{'='*70}")
        print(f"📊 {sym}")
        print(f"{'='*70}")

        regime_counter = Counter()
        tf_attempts = 0
        tf_fires = 0

        for idx in range(100, len(candles), 5):
            window = candles[:idx+1]
            r = detect_regime(window)
            regime_counter[r.regime.value] += 1

            if r.regime.value == "trending_up":
                sig = evaluate_entry(window, cfg)
                if sig and sig.should_enter:
                    tf_fires += 1
                    if tf_fires <= 5:  # فقط 5 تای اول
                        print(f"  ✅ FIRE @ idx={idx}: entry={sig.entry_price:.2f}, "
                              f"sl={sig.initial_sl:.2f}, conf={sig.confidence}, "
                              f"adx={sig.adx:.1f}")
                else:
                    tf_attempts += 1

        print(f"  📈 توزیع رژیم‌ها: {dict(regime_counter)}")
        print(f"  🎯 trending_up: {regime_counter['trending_up']} بار")
        print(f"  ❌ تلاش ناموفق tf_entry: {tf_attempts}")
        print(f"  ✅ fire موفق: {tf_fires}")


if __name__ == "__main__":
    asyncio.run(main())
