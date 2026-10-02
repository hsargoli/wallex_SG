"""تست سریع اتصال به والکس — فقط برای dev."""

import asyncio

import httpx

from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger


async def main() -> None:
    configure_logging()
    log = get_logger("check_wallex")
    settings = get_settings()

    log.info("config_loaded", env=settings.ENV, base_url=settings.WALLEX_BASE_URL)

    headers = {"x-api-key": settings.WALLEX_API_KEY}

    async with httpx.AsyncClient(
        base_url=settings.WALLEX_BASE_URL,
        headers=headers,
        timeout=settings.WALLEX_TIMEOUT_SECONDS,
    ) as client:
        # ۱) endpoint عمومی — همه مارکت‌ها
        r = await client.get("/v1/markets")
        log.info("markets_status", status=r.status_code)
        if r.status_code == 200:
            data = r.json()
            markets = data.get("result", {}).get("symbols", {})
            log.info("markets_count", count=len(markets))
            first = next(iter(markets.items()), None)
            if first:
                log.info("sample_market", symbol=first[0], data=first[1])

        # ۲) endpoint خصوصی — موجودی حساب (نیاز به API Key)
        r = await client.get("/v1/account/balances")
        log.info("balances_status", status=r.status_code)
        if r.status_code == 200:
            data = r.json()
            balances = data.get("result", {}).get("balances", {})
            log.info("balances_count", count=len(balances))
        else:
            log.warning("balances_error", body=r.text[:300])


if __name__ == "__main__":
    asyncio.run(main())
