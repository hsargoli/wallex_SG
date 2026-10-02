"""دیباگ regime detector — ببینیم چرا همه چی choppy میشه."""
import asyncio
from collections import Counter

from app.application.use_cases.get_candles import GetCandlesUseCase
from app.core.config import get_settings
from app.infrastructure.exchange.wallex.client import WallexExchange
from app.services.regime_detector import detect_regime, calculate_adx
from app.services.indicators import atr, ema

SYMBOLS = ["BTCTMN", "ETHTMN", "XRPTMN", "ZECTMN", "SOLTMN"]
TF = "1h"
N = 2000


async def fetch_one(sym, settings):
    ex = WallexExchange.create(settings)
    try:
        uc = GetCandlesUseCase(exchange=ex)
        c = await uc.execute(symbol=sym, timeframe=TF, limit=N)
        return sym, c
    finally:
        await ex.aclose()


async def main():
    settings = get_settings()
    results = await asyncio.gather(*[fetch_one(s, settings) for s in SYMBOLS])

    for sym, candles in results:
        if not candles:
            print(f"❌ {sym}: no data")
            continue

        print(f"\n{'='*70}")
        print(f"📊 {sym} — {len(candles)} کندل")
        print(f"{'='*70}")

        # نمونه‌گیری هر 100 کندل
        regime_count = Counter()
        rows = []
        for idx in range(100, len(candles), 100):
            window = candles[:idx+1]
            r = detect_regime(window)
            regime_count[r.regime.value] += 1

            adx = r.adx
            atr_pct = r.atr_pct
            # ret_20
            c = window
            ret_20 = (float(c[-1].close) - float(c[-21].close)) / float(c[-21].close) * 100

            rows.append((idx, adx, atr_pct, ret_20, r.regime.value, r.ema_alignment, r.confidence))

        print(f"  {'idx':>5} {'ADX':>6} {'ATR%':>6} {'ret20%':>7} {'regime':<14} {'ema':<12} {'conf':>4}")
        print(f"  {'─'*70}")
        for row in rows[:15]:  # فقط 15 تای اول
            idx, adx, atr_pct, ret_20, reg, ema_al, conf = row
            print(f"  {idx:>5} {adx:>6.1f} {atr_pct:>6.2f} {ret_20:>+7.2f} {reg:<14} {ema_al:<12} {conf:>4}")

        print(f"\n  📈 توزیع رژیم‌ها: {dict(regime_count)}")


if __name__ == "__main__":
    asyncio.run(main())
