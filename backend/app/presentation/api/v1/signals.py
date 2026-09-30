"""Signals & Indicators endpoints."""

from fastapi import APIRouter, HTTPException, status

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
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e

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
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e

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
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e

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
