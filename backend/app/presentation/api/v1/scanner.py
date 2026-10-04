"""Scanner — اسکن مارکت‌ها با صفحه‌بندی بر اساس حجم."""

import asyncio

from fastapi import APIRouter, Query

from app.application.use_cases.get_candles import GetCandlesUseCase
from app.presentation.api.deps import ExchangeDep
from app.services.signal_engine import generate_signal
from app.services.trend import analyze_trend
from app.services.indicators import atr, rsi

router = APIRouter(prefix="/scanner", tags=["Scanner"])

MAX_CONCURRENT = 10


async def _scan_one(use_case, symbol: str, sem: asyncio.Semaphore, tf: str = "1h") -> dict | None:
    async with sem:
        try:
            from decimal import Decimal as D

            # از 1h استفاده می‌کنیم تا تغییرات ۳/۱۲/۲۴ ساعته دقیق باشه
            candles = await use_case.execute(symbol=symbol, timeframe=tf, limit=200)
            if not candles or len(candles) < 100:
                return None

            trend = analyze_trend(candles)
            signal = generate_signal(candles)

            last_close = candles[-1].close

            # ---------- تغییرات ----------
            def _change(back: int) -> str | None:
                if len(candles) < back + 1:
                    return None
                ref = candles[-(back + 1)].close
                if ref == 0:
                    return None
                pct = (last_close / ref - D(1)) * D(100)
                return str(pct.quantize(D("0.01")))

            change_3h = _change(3)
            change_12h = _change(12)
            change_24h = _change(24)

            # ---------- Sparkline: ۲۴ کندل آخر ----------
            sparkline = [float(c.close) for c in candles[-24:]]

            # ---------- اندیکاتورها ----------
            rsi_vals = rsi(candles, 14)
            atr_vals = atr(candles, 14)
            rsi_14 = (
                str(rsi_vals[-1].quantize(D("0.01")))
                if rsi_vals and rsi_vals[-1] is not None
                else None
            )
            atr_14 = (
                str(atr_vals[-1].quantize(D("0.01")))
                if atr_vals and atr_vals[-1] is not None
                else None
            )
            atr_pct = None
            if atr_14 is not None and last_close > 0:
                atr_pct = str(
                    ((atr_vals[-1] / last_close) * D(100)).quantize(D("0.01"))
                )

            return {
                "symbol": symbol,
                "current_price": str(last_close),
                "trend_score": trend.score,
                "direction": trend.direction,
                "strength": trend.strength,
                "pattern": trend.pattern,
                "volatility_pct": str(trend.volatility_pct.quantize(D("0.01"))),
                "ema_alignment": trend.ema_alignment,
                "reasons": trend.reasons,
                "change_3h": change_3h,
                "change_12h": change_12h,
                "change_24h": change_24h,
                "signal": signal.type.value,
                "risk_reward": (
                    str(signal.risk_reward.quantize(D("0.01"))) if signal.risk_reward else None
                ),
                "sparkline": sparkline,
                "rsi_14": rsi_14,
                "atr_14": atr_14,
                "atr_pct": atr_pct,
            }
        except Exception:
            return None


def _vol_key(m) -> float:
    """استخراج حجم ۲۴ ساعته از market."""
    try:
        stats = getattr(m, "stats", None)
        if stats and stats.daily_quote_volume:
            return float(stats.daily_quote_volume)
    except Exception:
        pass
    return 0.0


@router.get("/list")
async def list_markets_paginated(
    exchange: ExchangeDep,
    quote: str = Query("TMN", description="ارز پایه"),
    page: int = Query(1, ge=1),
    page_size: int = Query(15, ge=5, le=30),
):
    """
    لیست مارکت‌ها با صفحه‌بندی بر اساس حجم ۲۴ ساعته.
    برمی‌گردونه: metadata + نمادهای صفحه‌ی جاری (بدون اسکن).
    """
    all_markets = await exchange.get_markets()
    quote_upper = quote.upper()

    # فیلتر بر اساس quote و داشتن stats
    filtered = [
        m
        for m in all_markets
        if str(m.symbol).upper().endswith(quote_upper) and getattr(m, "stats", None) is not None
    ]

    # مرتب‌سازی بر اساس حجم (بالاترین اول)
    filtered.sort(key=_vol_key, reverse=True)

    total = len(filtered)
    total_pages = max(1, (total + page_size - 1) // page_size)

    # صفحه‌ی جاری
    start = (page - 1) * page_size
    end = start + page_size
    page_items = filtered[start:end]

    symbols = [str(m.symbol) for m in page_items]

    # اطلاعات حجم برای نمایش
    items_meta = [
        {
            "symbol": str(m.symbol),
            "quote": str(m.quote_asset),
            "daily_volume": str(getattr(m.stats, "daily_quote_volume", 0) or 0),
        }
        for m in page_items
    ]

    return {
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": total_pages,
        "quote": quote,
        "symbols": symbols,
        "items_meta": items_meta,
    }


@router.get("/scan")
async def scan_page(
    exchange: ExchangeDep,
    symbols: str = Query(..., description="نمادها با کاما جدا شده"),
    tf: str = Query("1h", description="تایم‌فریم: 15m, 1h, 4h, 1D"),
):
    """اسکن نمادهای داده‌شده (برای صفحه‌ی جاری)."""
    sym_list = [s.strip().upper() for s in symbols.split(",") if s.strip()][:30]
    if not sym_list:
        return {"count": 0, "items": []}

    use_case = GetCandlesUseCase(exchange=exchange)
    sem = asyncio.Semaphore(MAX_CONCURRENT)
    tasks = [_scan_one(use_case, sym, sem, tf=tf) for sym in sym_list]
    results = await asyncio.gather(*tasks)

    items = [r for r in results if r is not None]
    # ترتیب اصلی (بر اساس حجم از /list) حفظ می‌شود

    return {"count": len(items), "timeframe": tf, "items": items}
