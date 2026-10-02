"""تست سریع کف‌شناس روی داده‌ی واقعی."""

import asyncio
import time
from decimal import Decimal

from app.application.use_cases.get_candles import GetCandlesUseCase
from app.core.config import get_settings
from app.infrastructure.exchange.wallex.client import WallexExchange
from app.services.bottom_detector import detect_bottom


async def main():
    settings = get_settings()
    ex = WallexExchange.create(settings)
    try:
        uc = GetCandlesUseCase(exchange=ex)
        symbol = "BTCTMN"
        tf = "1h"
        candles = await uc.execute(symbol=symbol, timeframe=tf, limit=800)
        print(f"📊 {symbol} ({tf}) — {len(candles)} کندل\n")

        detections = []
        # از کندل 50 به بعد (warmup)
        for i in range(50, len(candles)):
            sig = detect_bottom(candles, idx=i)
            if sig.is_bottom:
                detections.append((i, sig))

        print(f"🎯 تعداد کف تشخیص داده‌شده: {len(detections)}\n")

        if not detections:
            return

        # بررسی نتیجه: قیمت بعدش چقدر رفت بالا؟
        print("جزئیات کف‌ها (نتیجه در 24 کندل بعد):")
        print("-" * 80)

        correct = 0
        strong_correct = 0
        strong_total = 0

        for idx, sig in detections:
            # 24 کندل بعد
            future = candles[idx + 1 : idx + 25]
            if not future:
                continue

            max_high = max(c.high for c in future)
            min_low = min(c.low for c in future)
            entry_price = candles[idx].close

            max_gain_pct = float((max_high - entry_price) / entry_price * 100)
            max_loss_pct = float((min_low - entry_price) / entry_price * 100)

            # آیا در 24 کندل بعد +1.5% سود رفته؟ (موفق)
            success = max_gain_pct >= 1.5

            if success:
                correct += 1

            if sig.strength == "strong":
                strong_total += 1
                if success:
                    strong_correct += 1

            mark = "✅" if success else "❌"
            ts = time.strftime("%m-%d %H:%M", time.gmtime(candles[idx].time))
            print(f"  {mark} {ts}  score={sig.score:>2}  {sig.strength:>6}  gain={max_gain_pct:>+5.2f}%  loss={max_loss_pct:>+5.2f}%  | {sig.reasons[0] if sig.reasons else '—'}")

        print()
        print("=" * 80)
        print(f"📈 دقت کل:           {correct}/{len(detections)}  = {correct/len(detections)*100:.1f}%")
        if strong_total > 0:
            print(f"📈 دقت کف‌های قوی:    {strong_correct}/{strong_total}  = {strong_correct/strong_total*100:.1f}%")
    finally:
        await ex.aclose()


if __name__ == "__main__":
    asyncio.run(main())
