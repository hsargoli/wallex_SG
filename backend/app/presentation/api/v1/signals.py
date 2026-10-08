"""Signals & Indicators endpoints."""

import asyncio

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.application.use_cases.get_candles import GetCandlesUseCase
from app.presentation.api.deps import ExchangeDep
from app.services.indicators import (
    atr,
    bollinger,
    ema,
    macd,
    rsi,
    sma,
    volume_sma,
)
from app.services.levels import find_swing_levels, pivot_from_candles
from app.services.signal_engine import generate_signal

router = APIRouter(prefix="/signals", tags=["Signals"])


def _candle_to_dict(c) -> dict:
    return {
        "time": c.time,
        "open": str(c.open),
        "high": str(c.high),
        "low": str(c.low),
        "close": str(c.close),
        "volume": str(c.volume),
    }


def _ds(v) -> str | None:
    return None if v is None else str(v)


def _ds_list(values) -> list[str | None]:
    return [_ds(v) for v in values]


@router.get("/indicators/{symbol}")
async def get_indicators(
    symbol: str,
    exchange: ExchangeDep,
    tf: str = "1h",
    limit: int = 200,
):
    """محاسبه‌ی همه‌ی اندیکاتورها برای یک نماد."""
    try:
        use_case = GetCandlesUseCase(exchange=exchange)
        candles = await use_case.execute(symbol=symbol, timeframe=tf, limit=limit)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    if not candles:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"داده‌ای برای {symbol} یافت نشد",
        )

    macd_line, macd_signal, macd_hist = macd(candles)
    bb_upper, bb_middle, bb_lower = bollinger(candles)

    return {
        "symbol": symbol,
        "timeframe": tf,
        "count": len(candles),
        "candles": [_candle_to_dict(c) for c in candles],
        "sma_20": _ds_list(sma(candles, 20)),
        "sma_50": _ds_list(sma(candles, 50)),
        "ema_9": _ds_list(ema(candles, 9)),
        "ema_21": _ds_list(ema(candles, 21)),
        "rsi_14": _ds_list(rsi(candles, 14)),
        "volume_ma_20": _ds_list(volume_sma(candles, 20)),
        "macd": _ds_list(macd_line),
        "macd_signal": _ds_list(macd_signal),
        "macd_hist": _ds_list(macd_hist),
        "bb_upper": _ds_list(bb_upper),
        "bb_middle": _ds_list(bb_middle),
        "bb_lower": _ds_list(bb_lower),
        "atr_14": _ds_list(atr(candles, 14)),
    }


# ============================================================
# Batch Signals
# ============================================================


class BatchSignalsRequest(BaseModel):
    """درخواست سیگنال چندگانه."""

    symbols: list[str] = Field(..., min_length=1, max_length=20)
    tf: str = Field("1h", description="تایم‌فریم")
    limit: int = Field(200, ge=50, le=500)


class BatchSignalItem(BaseModel):
    """یک سیگنال در پاسخ batch."""

    symbol: str
    signal: str
    strength: str
    confidence: int
    current_price: str
    reasons: list[str] = []
    buy_score: int = 0
    sell_score: int = 0
    stop_loss: str | None = None
    take_profit: str | None = None
    risk_reward: str | None = None
    # Sparkline (آخرین N قیمت close — برای نمایش نمودار کوچک)
    sparkline: list[float] = []
    # تغییرات قیمت
    change_24h: float | None = None
    change_7d: float | None = None
    change_1h: float | None = None
    change_1m: float | None = None
    error: str | None = None


class BatchSignalsResponse(BaseModel):
    """پاسخ batch."""

    timeframe: str
    count: int
    signals: list[BatchSignalItem]


async def _fetch_signal_for(
    use_case: GetCandlesUseCase,
    symbol: str,
    tf: str,
    limit: int,
    semaphore: asyncio.Semaphore,
    market_map: dict | None = None,
) -> dict:
    """دریافت candles + تولید سیگنال برای یک نماد (با محدودیت هم‌زمانی).

    market_map (اختیاری): {symbol: Market} از Wallex.
    اگه داده بشه، change_24h/7d از Wallex گرفته می‌شن — هماهنگ با /v1/markets.
    """
    async with semaphore:
        try:
            candles = await use_case.execute(symbol=symbol, timeframe=tf, limit=limit)
            if not candles:
                return {"symbol": symbol, "error": "no_data"}

            sig = generate_signal(candles)

            # Sparkline: آخرین 30 کندل close
            recent = candles[-30:] if len(candles) >= 30 else candles
            sparkline = [float(c.close) for c in recent]

            # تغییر 24h — منبع واحد: Wallex (هماهنگ با /v1/markets)
            market = (market_map or {}).get(symbol)
            change_24h = None
            if market is not None and getattr(market, "stats", None):
                dcp = getattr(market.stats, "daily_change_percent", None)
                if dcp is not None:
                    change_24h = float(dcp)
            # fallback: محاسبه از کندل‌ها
            if change_24h is None and len(candles) >= 25:
                old_price = float(candles[-25].close)
                if old_price > 0:
                    change_24h = round(
                        (float(candles[-1].close) - old_price) / old_price * 100, 2
                    )

            # تغییر 7d — منبع واحد: Wallex
            change_7d = None
            if market is not None and getattr(market, "stats", None):
                wcp = getattr(market.stats, "weekly_change_percent", None)
                if wcp is not None:
                    change_7d = float(wcp)
            # fallback: محاسبه از کندل‌ها
            if change_7d is None and len(candles) >= 169:
                old_price = float(candles[-169].close)
                if old_price > 0:
                    change_7d = round(
                        (float(candles[-1].close) - old_price) / old_price * 100, 2
                    )

            # تغییر 1h: مقایسه آخرین با کندل قبلی
            change_1h = None
            if len(candles) >= 2:
                old_price = float(candles[-2].close)
                if old_price > 0:
                    change_1h = round(
                        (float(candles[-1].close) - old_price) / old_price * 100, 2
                    )

            # تغییر 1m: مقایسه آخرین با کندل 696 ساعت قبل (29 روز × 24)
            # والکس فقط 29 روز کندل می‌دهد — به همین دلیل 1m (نه 30d)
            change_1m = None
            if len(candles) >= 697:
                old_price = float(candles[-697].close)
                if old_price > 0:
                    change_1m = round(
                        (float(candles[-1].close) - old_price) / old_price * 100, 2
                    )

            return {
                "symbol": symbol,
                "signal": sig.type.value,
                "strength": sig.strength.value,
                "confidence": sig.confidence,
                "current_price": str(sig.current_price),
                "reasons": sig.reasons[:3],
                "buy_score": sig.buy_score,
                "sell_score": sig.sell_score,
                "stop_loss": _ds(sig.stop_loss),
                "take_profit": _ds(sig.take_profit),
                "risk_reward": _ds(sig.risk_reward),
                "sparkline": sparkline,
                "change_24h": change_24h,
                "change_7d": change_7d,
                "change_1h": change_1h,
                "change_1m": change_1m,
            }
        except Exception as e:
            return {"symbol": symbol, "error": str(e)[:120]}


@router.post("/batch", response_model=BatchSignalsResponse)
async def get_batch_signals(
    payload: BatchSignalsRequest,
    exchange: ExchangeDep,
):
    """تولید سیگنال برای چندین نماد به‌صورت موازی.

    - حداکثر 20 نماد در هر درخواست
    - حداکثر 5 درخواست هم‌زمان به والکس (برای رعایت rate limit)
    """
    use_case = GetCandlesUseCase(exchange=exchange)
    semaphore = asyncio.Semaphore(5)

    # دریافت یک‌باره‌ی Marketها برای change_24h/7d (منبع واحد با /v1/markets)
    market_map: dict = {}
    try:
        markets = await exchange.get_markets()
        market_map = {str(m.symbol).upper(): m for m in markets}
    except Exception:
        pass  # fallback به محاسبه از کندل‌ها

    tasks = [
        _fetch_signal_for(use_case, sym, payload.tf, payload.limit, semaphore, market_map)
        for sym in payload.symbols
    ]
    results = await asyncio.gather(*tasks)

    # مرتب‌سازی: موفق‌ها اول، بعد خطاها
    results.sort(key=lambda x: (x.get("error") is not None,))

    return {
        "timeframe": payload.tf,
        "count": len(results),
        "signals": results,
    }


@router.get("/{symbol}")
async def get_signal(
    symbol: str,
    exchange: ExchangeDep,
    tf: str = "1h",
    limit: int = 200,
):
    """تولید سیگنال خرید/فروش برای یک نماد."""
    try:
        use_case = GetCandlesUseCase(exchange=exchange)
        candles = await use_case.execute(symbol=symbol, timeframe=tf, limit=limit)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    if not candles:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"داده‌ای برای {symbol} یافت نشد",
        )

    signal = generate_signal(candles)

    return {
        "symbol": symbol,
        "timeframe": tf,
        "signal": signal.type.value,
        "strength": signal.strength.value,
        "confidence": signal.confidence,
        "current_price": str(signal.current_price),
        "reasons": signal.reasons,
        "rules": [
            {
                "name": r.name,
                "passed": r.passed,
                "score": r.score,
                "reason": r.reason,
            }
            for r in signal.rules
        ],
        "buy_score": signal.buy_score,
        "sell_score": signal.sell_score,
        "stop_loss": _ds(signal.stop_loss),
        "take_profit": _ds(signal.take_profit),
        "risk_reward": _ds(signal.risk_reward),
        "indicators": {k: _ds(v) for k, v in signal.indicators.items()},
    }


@router.get("/levels/{symbol}")
async def get_levels(
    symbol: str,
    exchange: ExchangeDep,
    tf: str = "1h",
    limit: int = 500,
):
    """سطوح کلیدی: Pivot Points و Support/Resistance."""
    try:
        use_case = GetCandlesUseCase(exchange=exchange)
        candles = await use_case.execute(symbol=symbol, timeframe=tf, limit=limit)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    if not candles:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"داده‌ای برای {symbol} یافت نشد",
        )

    # Pivot
    pivot = pivot_from_candles(candles)

    # S/R
    swings = find_swing_levels(candles, lookback=5, tolerance_pct=0.5)

    current_price = candles[-1].close

    return {
        "symbol": symbol,
        "timeframe": tf,
        "current_price": str(current_price),
        "pivot": (
            {
                "pp": str(pivot.pp),
                "r1": str(pivot.r1),
                "r2": str(pivot.r2),
                "r3": str(pivot.r3),
                "s1": str(pivot.s1),
                "s2": str(pivot.s2),
                "s3": str(pivot.s3),
                "basis_high": str(pivot.basis_high),
                "basis_low": str(pivot.basis_low),
                "basis_close": str(pivot.basis_close),
            }
            if pivot
            else None
        ),
        "swings": [
            {
                "price": str(s.price),
                "type": s.type,
                "touches": s.touches,
                "last_time": s.last_time,
                "strength": s.strength,
                "distance_pct": str(
                    ((current_price - s.price) / current_price * 100).quantize(
                        __import__("decimal").Decimal("0.01")
                    )
                ),
            }
            for s in swings
        ],
    }


@router.get("/{symbol}/multi")
async def get_multi_timeframe_signals(
    symbol: str,
    exchange: ExchangeDep,
):
    """سیگنال در چند تایم‌فریم — برای تأیید متقابل."""
    use_case = GetCandlesUseCase(exchange=exchange)
    result = {}
    buy_count = 0
    sell_count = 0
    hold_count = 0

    for tf in ["15m", "1h", "4h", "1D"]:
        try:
            candles = await use_case.execute(symbol=symbol, timeframe=tf, limit=200)
            if candles:
                sig = generate_signal(candles)
                result[tf] = {
                    "signal": sig.type.value,
                    "strength": sig.strength.value,
                    "confidence": sig.confidence,
                    "reasons": sig.reasons,
                    "buy_score": sig.buy_score,
                    "sell_score": sig.sell_score,
                }
                if sig.type.value == "buy":
                    buy_count += 1
                elif sig.type.value == "sell":
                    sell_count += 1
                else:
                    hold_count += 1
            else:
                result[tf] = {"signal": "no_data"}
        except Exception as e:
            result[tf] = {"signal": "error", "message": str(e)}

    # خلاصه‌ی Confluence
    total = buy_count + sell_count
    if total == 0:
        confluence = "neutral"
        confluence_label = "بی‌طرف"
    elif buy_count >= 3:
        confluence = "strong_buy"
        confluence_label = f"خرید قوی ({buy_count}/4 تایم‌فریم)"
    elif sell_count >= 3:
        confluence = "strong_sell"
        confluence_label = f"فروش قوی ({sell_count}/4 تایم‌فریم)"
    elif buy_count == 2 and sell_count <= 1:
        confluence = "lean_buy"
        confluence_label = "تمایل به خرید"
    elif sell_count == 2 and buy_count <= 1:
        confluence = "lean_sell"
        confluence_label = "تمایل به فروش"
    else:
        confluence = "mixed"
        confluence_label = "متضاد — صبر کن"

    return {
        "symbol": symbol,
        "timeframes": result,
        "confluence": {
            "status": confluence,
            "label": confluence_label,
            "buy_count": buy_count,
            "sell_count": sell_count,
            "hold_count": hold_count,
        },
    }
