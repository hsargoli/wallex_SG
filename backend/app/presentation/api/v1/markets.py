"""Endpointهای بازار."""

from fastapi import APIRouter

from app.application.use_cases.get_market import GetMarketUseCase
from app.application.use_cases.get_markets import GetMarketsUseCase
from app.domain.entities.market import Market
from app.infrastructure.exchange.wallex.mapper import map_order_book
from app.presentation.api.deps import ExchangeDep
from app.presentation.api.v1.schemas import (
    MarketOut,
    MarketsResponse,
    OrderBookResponse,
)

router = APIRouter(prefix="/markets", tags=["markets"])


def _to_out(m: Market) -> MarketOut:
    stats = m.stats
    data = {
        "symbol": str(m.symbol),
        "base_asset": m.base_asset,
        "quote_asset": m.quote_asset,
        "last_price": m.last_price,
        "fa_name": m.fa_name,
        "en_name": m.en_name,
        "daily_volume": stats.daily_volume if stats else None,
        "daily_quote_volume": stats.daily_quote_volume if stats else None,
        "daily_change_percent": stats.daily_change_percent if stats else None,
    }
    return MarketOut.model_validate(data)


@router.get("", response_model=MarketsResponse)
async def list_markets(exchange: ExchangeDep) -> MarketsResponse:
    """دریافت همه مارکت‌های فعال والکس."""
    use_case = GetMarketsUseCase(exchange=exchange)
    markets = await use_case.execute()
    items = [_to_out(m) for m in markets]
    return MarketsResponse(count=len(items), items=items)


@router.get("/{symbol}", response_model=MarketOut)
async def get_market(symbol: str, exchange: ExchangeDep) -> MarketOut:
    """دریافت اطلاعات یک مارکت مشخص."""
    use_case = GetMarketUseCase(exchange=exchange)
    market = await use_case.execute(symbol)
    return _to_out(market)


@router.get("/orderbook/{symbol}", response_model=OrderBookResponse)
async def get_order_book_endpoint(symbol: str, exchange: ExchangeDep):
    """دریافت دفتر سفارشات یک نماد."""
    raw_data = await exchange.get_order_book(symbol=symbol)
    return map_order_book(raw_data, symbol=symbol)


@router.get("/candles/{symbol}")
async def get_candles_endpoint(
    symbol: str,
    exchange: ExchangeDep,
    tf: str = "1h",
    limit: int = 500,
):
    """دریافت کندل‌های تاریخی OHLCV.

    Args:
        symbol: نماد (مثل BTCTMN)
        tf: تایم‌فریم (15m, 1h, 4h, 1D)
        limit: تعداد کندل (حداکثر ۳۰۰۰)
    """
    from app.application.use_cases.get_candles import GetCandlesUseCase

    try:
        use_case = GetCandlesUseCase(exchange=exchange)
        candles = await use_case.execute(symbol=symbol, timeframe=tf, limit=limit)
    except ValueError as e:
        from fastapi import HTTPException, status

        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    return {
        "symbol": symbol,
        "timeframe": tf,
        "count": len(candles),
        "candles": [
            {
                "time": c.time,
                "open": str(c.open),
                "high": str(c.high),
                "low": str(c.low),
                "close": str(c.close),
                "volume": str(c.volume),
            }
            for c in candles
        ],
    }


@router.get("/candles-v2/{symbol}")
async def get_candles_v2_endpoint(
    symbol: str,
    exchange: ExchangeDep,
    tf: str = "1h",
    limit: int = 500,
):
    """دریافت کندل با شبیه‌سازی بازه‌های خالی از تایم‌فریم بالاتر.

    - 15m: فقط دیتای واقعی (محدود به 500 کندل)
    - 1h: دیتای واقعی + شبیه‌سازی از 1D
    - 4h: کاملاً شبیه‌سازی از 1D
    - 1D: مستقیم

    نواحی شبیه‌سازی‌شده در `synthetic_ranges` برگردانده می‌شوند.
    """
    from app.application.use_cases.get_candles_with_fallback import (
        GetCandlesWithFallbackUseCase,
    )

    try:
        use_case = GetCandlesWithFallbackUseCase(exchange=exchange)
        result = await use_case.execute(symbol=symbol, timeframe=tf, limit=limit)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    return {
        "symbol": symbol,
        "timeframe": result.requested_tf,
        "count": len(result.candles),
        "real_count": result.real_candles_count,
        "synthetic_count": result.synthetic_candles_count,
        "candles": [
            {
                "time": c.time,
                "open": str(c.open),
                "high": str(c.high),
                "low": str(c.low),
                "close": str(c.close),
                "volume": str(c.volume),
            }
            for c in result.candles
        ],
        "synthetic_ranges": [
            {
                "from_ts": r.from_ts,
                "to_ts": r.to_ts,
                "source_tf": r.source_tf,
            }
            for r in result.synthetic_ranges
        ],
    }



@router.get("/facts/{symbol}")
async def get_facts_endpoint(
    symbol: str,
    exchange: ExchangeDep,
):
    """فکت‌های تحلیلی چهار‌دوره‌ای برای یک نماد.

    - بلندمدت (۱ سال): از 1D
    - میان‌مدت (۲۹ روز): از 1h
    - نوسان هفتگی (۷ روز): از 1h (زیرمجموعه)
    - لحظه‌ای (۸ ساعت): از 1m → 15m
    """
    from app.application.use_cases.get_candles import GetCandlesUseCase
    from app.services.candle_aggregator import aggregate_candles
    from app.services.facts import (
        compute_period_facts,
        compute_overall_summary,
    )

    use_case = GetCandlesUseCase(exchange=exchange)

    # ─── ۱) 1D: ۱ سال ───
    daily = await _safe_fetch(use_case, symbol, "1D", 365)

    # ─── ۲) 1h: ۲۹ روز ───
    hourly = await _safe_fetch(use_case, symbol, "1h", 700)

    # ─── ۳) 1m → 15m: ۸ ساعت ───
    raw_1m = await _fetch_1m_direct(exchange, symbol, limit=500)
    m15 = aggregate_candles(raw_1m, factor=15) if raw_1m else []

    # ─── محاسبه‌ی فکت‌ها ───
    # بازه ۳ (۷ روز) = زیرمجموعه 1h (آخرین ۱۶۸ کندل)
    hourly_7d = hourly[-168:] if len(hourly) > 168 else hourly

    period_configs = [
        ("1y", "1D", daily),           # بلندمدت
        ("1mo", "1h", hourly),         # میان‌مدت (۲۹ روز)
        ("7d", "1h", hourly_7d),       # نوسان هفتگی
        ("8h", "15m", m15),            # لحظه‌ای
    ]

    periods_out = []
    for period, tf, candles in period_configs:
        facts = compute_period_facts(candles, period=period, timeframe=tf)
        if facts is None:
            periods_out.append(
                {
                    "period": period,
                    "timeframe": tf,
                    "available": False,
                }
            )
            continue

        periods_out.append(
            {
                "period": period,
                "timeframe": tf,
                "available": True,
                "candles_count": facts.candles_count,
                "change_pct": str(facts.change_pct),
                "first_price": str(facts.first_price),
                "last_price": str(facts.last_price),
                "high_price": str(facts.high_price),
                "high_time": facts.high_time,
                "low_price": str(facts.low_price),
                "low_time": facts.low_time,
                "volatility_pct": str(facts.volatility_pct),
                "max_drop_pct": str(facts.max_drop_pct),
                "max_rise_pct": str(facts.max_rise_pct),
                "avg_range_pct": str(facts.avg_range_pct),
                "daily_vol_pct": str(facts.daily_vol_pct),
                "pullback_count": facts.pullback_count,
                "pullback_avg_pct": str(facts.pullback_avg_pct),
                "swing_count": facts.swing_count,
                "biggest_rise_pct": str(facts.biggest_rise_pct),
                "biggest_rise_time": facts.biggest_rise_time,
                "biggest_drop_pct_swing": str(facts.biggest_drop_pct_swing),
                "biggest_drop_time": facts.biggest_drop_time,
                "interpretation": facts.interpretation,
                "trend_direction": facts.trend_direction,
                "trend_strength": facts.trend_strength,
                "trend_pattern": facts.trend_pattern,
                "trend_score": facts.trend_score,
                "avg_volume": str(facts.avg_volume),
                "volume_vs_avg": str(facts.volume_vs_avg),
                "facts": facts.facts,
            }
        )

    # ─── محاسبه‌ی خلاصه‌ی کلی ───
    # فقط دوره‌های available
    valid_periods = []
    for cfg, out in zip(period_configs, periods_out):
        if out.get("available"):
            # پیدا کردن PeriodFacts از دیتای ذخیره‌شده
            facts = compute_period_facts(cfg[2], period=cfg[0], timeframe=cfg[1])
            if facts:
                valid_periods.append(facts)

    summary = compute_overall_summary(valid_periods)

    return {
        "symbol": symbol,
        "periods": periods_out,
        "summary": {
            "overall_behavior": summary.overall_behavior,
            "outlook": summary.outlook,
            "risk_level": summary.risk_level,
            "advice": summary.advice,
            "consistency": summary.consistency,
        },
    }


async def _safe_fetch(use_case, symbol, tf, limit):
    """دریافت امن کندل از use case — در صورت خطا آرایه خالی."""
    try:
        return await use_case.execute(symbol=symbol, timeframe=tf, limit=limit)
    except Exception:
        return []


async def _fetch_1m_direct(exchange, symbol: str, limit: int = 500):
    """دریافت مستقیم کندل‌های 1m از exchange (چون use case پشتیبانی نمی‌کنه)."""
    import time

    try:
        now = int(time.time())
        # سقف ۵۰۰ کندل، حاشیه ۱۰٪
        needed = int(limit * 60 * 1.1)
        from_ts = now - needed

        candles = await exchange.get_candles(
            symbol=symbol,
            resolution="15",  # "15" = 1m (طبق کشف قبلی)
            from_ts=from_ts,
            to_ts=now,
        )
        return candles[-limit:] if candles else []
    except Exception:
        return []
