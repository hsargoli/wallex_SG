"""تست: چقدر داده می‌تونیم از Wallex بگیریم؟"""

import asyncio
import time
from datetime import datetime

from app.core.config import get_settings
from app.infrastructure.exchange.wallex.client import WallexExchange


async def main():
    settings = get_settings()
    ex = WallexExchange.create(settings)
    try:
        # تلاش برای ۳۰ روز اخیر
        now = int(time.time())
        print(f"🎯 تلاش برای دریافت ۳۰ روز 15m...")
        print(f"   انتظار: ~2880 کندل\n")

        # چند بازه مختلف تست کنیم
        ranges = [
            ("7 روز اخیر", 7),
            ("14 روز اخیر", 14),
            ("30 روز اخیر", 30),
            ("60 روز اخیر", 60),
        ]

        for label, days in ranges:
            from_ts = now - days * 86400
            raw = await ex.get_candles(
                symbol="BTCTMN", resolution="15",
                from_ts=from_ts, to_ts=now,
            )
            n = len(raw)
            print(f"  {label:15}  →  {n:>5} کندل")
            if raw:
                first_dt = datetime.fromtimestamp(raw[0].time)
                last_dt = datetime.fromtimestamp(raw[-1].time)
                print(f"                 از {first_dt.strftime('%Y-%m-%d %H:%M')}")
                print(f"                 تا {last_dt.strftime('%Y-%m-%d %H:%M')}")
    finally:
        await ex.aclose()


if __name__ == "__main__":
    asyncio.run(main())
