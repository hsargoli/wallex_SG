"""Backtest endpoint."""

from fastapi import APIRouter, HTTPException, status

from app.application.use_cases.get_candles import GetCandlesUseCase
from app.presentation.api.deps import ExchangeDep
from app.services.backtest import run_backtest

router = APIRouter(prefix="/backtest", tags=["Backtest"])


@router.get("/run/{symbol}")
async def run(
    symbol: str,
    exchange: ExchangeDep,
    tf: str = "1h",
    limit: int = 1000,
    min_confidence: int = 50,
    max_duration: int = 24,
):
    """اجرای backtest روی یک نماد."""
    try:
        use_case = GetCandlesUseCase(exchange=exchange)
        candles = await use_case.execute(symbol=symbol, timeframe=tf, limit=limit)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    if not candles or len(candles) < 150:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="داده کافی نیست (حداقل ۱۵۰ کندل لازم است)",
        )

    result = run_backtest(
        candles=candles,
        symbol=symbol,
        timeframe=tf,
        min_confidence=min_confidence,
        max_duration=max_duration,
    )

    recent_trades = [
        {
            "entry_time": t.entry_time,
            "exit_time": t.exit_time,
            "entry_price": str(t.entry_price),
            "exit_price": str(t.exit_price),
            "side": t.side,
            "return_pct": round(t.return_pct, 3),
            "duration_candles": t.duration_candles,
            "exit_reason": t.exit_reason,
            "confidence": t.confidence,
        }
        for t in result.trades[-20:]
    ]

    return {
        "symbol": result.symbol,
        "timeframe": result.timeframe,
        "candles_analyzed": result.candles_analyzed,
        "signals_generated": result.signals_generated,
        "stats": {
            "total_trades": result.total_trades,
            "wins": result.wins,
            "losses": result.losses,
            "win_rate": round(result.win_rate, 2),
            "avg_win_pct": round(result.avg_win_pct, 3),
            "avg_loss_pct": round(result.avg_loss_pct, 3),
            "total_return_pct": round(result.total_return_pct, 3),
            "profit_factor": round(result.profit_factor, 3),
            "max_drawdown_pct": round(result.max_drawdown_pct, 3),
            "sharpe_ratio": round(result.sharpe_ratio, 3),
            "avg_duration_candles": round(result.avg_duration_candles, 1),
        },
        "equity_curve": result.equity_curve,
        "recent_trades": recent_trades,
    }


@router.get("/bot/{bot_slug}/{symbol}")
async def run_bot(
    bot_slug: str,
    symbol: str,
    exchange: ExchangeDep,
    tf: str = "1h",
    limit: int = 1000,
    initial_capital: float = 1000.0,
    position_size_pct: float = 50.0,
    fee_pct: float = 0.2,
):
    """بک‌تست یک ربات روی داده‌ی گذشته (فعلاً فقط scalp_master)."""
    if bot_slug != "scalp_master":
        raise HTTPException(status_code=400, detail="فعلاً فقط scalp_master پشتیبانی می‌شود")

    from app.infrastructure.backtest.bot_backtest import run_scalp_backtest

    try:
        candles = await GetCandlesUseCase(exchange=exchange).execute(
            symbol=symbol, timeframe=tf, limit=limit
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    if not candles or len(candles) < 100:
        raise HTTPException(status_code=400, detail="داده کافی نیست (حداقل ۱۰۰ کندل)")

    result = run_scalp_backtest(
        candles,
        initial_capital=initial_capital,
        position_size_pct=position_size_pct,
        fee_pct=fee_pct,
    )
    for t in result["trades"]:
        t["symbol"] = symbol
    result["symbol"] = symbol
    result["timeframe"] = tf
    result["bot_slug"] = bot_slug
    return result


FALLBACK_SYMBOLS = [
    "NEARTMN", "SANDTMN", "ORCATMN", "BTCTMN", "ETHTMN", "SOLTMN", "XRPTMN",
    "DOGETMN", "ADATMN", "TRXTMN", "LTCTMN", "LINKTMN", "AVAXTMN", "DOTTMN", "SHIBTMN",
]


async def _pick_symbols(exchange, n: int) -> tuple[list[str], str]:
    """۱۵ نماد TMN با بیشترین حجم؛ در صورت شکست، لیست ثابت."""
    try:
        markets = await exchange.get_markets()
        rows = []
        for m in markets:
            sym = getattr(m, "symbol", None)
            if not sym or not str(sym).endswith("TMN"):
                continue
            vol = 0.0
            for f in ("volume_24h", "quote_volume", "volume", "quote_volume_24h"):
                v = getattr(m, f, None)
                if v is not None:
                    try:
                        vol = float(v)
                        break
                    except (TypeError, ValueError):
                        pass
            rows.append((vol, str(sym)))
        if rows and any(v > 0 for v, _ in rows):
            rows.sort(reverse=True)
            return [sym for _, sym in rows[:n]], "markets_by_volume"
    except Exception:
        pass
    return FALLBACK_SYMBOLS[:n], "fallback_list"


@router.get("/bot/{bot_slug}")
async def run_bot_multi(
    bot_slug: str,
    exchange: ExchangeDep,
    symbols: str = "",
    top: int = 15,
    tf: str = "1h",
    limit: int = 3000,
    initial_capital: float = 1000.0,
    position_size_pct: float = 50.0,
    fee_pct: float = 0.2,
):
    """بک‌تست چندنمادی (سرمایه‌ی مستقل برای هر نماد)."""
    import asyncio

    if bot_slug != "scalp_master":
        raise HTTPException(status_code=400, detail="فعلاً فقط scalp_master پشتیبانی می‌شود")

    from app.infrastructure.backtest.bot_backtest import run_scalp_backtest

    if symbols.strip():
        syms = [x.strip().upper() for x in symbols.split(",") if x.strip()]
        source = "manual"
    else:
        syms, source = await _pick_symbols(exchange, max(1, min(top, 30)))

    sem = asyncio.Semaphore(4)

    async def one(sym: str) -> dict:
        async with sem:
            try:
                candles = await GetCandlesUseCase(exchange=exchange).execute(
                    symbol=sym, timeframe=tf, limit=limit
                )
                if not candles or len(candles) < 100:
                    return {"symbol": sym, "error": "داده کافی نیست"}
                r = await asyncio.to_thread(
                    run_scalp_backtest, candles,
                    initial_capital=initial_capital,
                    position_size_pct=position_size_pct,
                    fee_pct=fee_pct,
                )
                for t in r["trades"]:
                    t["symbol"] = sym
                r["symbol"] = sym
                return r
            except Exception as e:
                return {"symbol": sym, "error": f"{type(e).__name__}: {e}"}

    results = await asyncio.gather(*(one(x) for x in syms))
    ok = [r for r in results if "error" not in r]
    failed = [{"symbol": r["symbol"], "error": r["error"]} for r in results if "error" in r]

    all_trades = sorted(
        (t for r in ok for t in r["trades"]), key=lambda t: t["entry_time"]
    )
    wins = [t for t in all_trades if t["pnl"] > 0]
    losses = [t for t in all_trades if t["pnl"] <= 0]
    gw = sum(t["pnl"] for t in wins)
    gl = abs(sum(t["pnl"] for t in losses))
    n = len(all_trades)

    per_symbol = [
        {
            "symbol": r["symbol"],
            "candles": r["candles_analyzed"],
            "trades": r["total_trades"],
            "win_rate": r["win_rate"],
            "pnl_pct": r["total_pnl_pct"],
            "profit_factor": r["profit_factor"],
            "max_drawdown_pct": r["max_drawdown_pct"],
        }
        for r in ok
    ]
    per_symbol.sort(key=lambda x: x["pnl_pct"], reverse=True)

    return {
        "bot_slug": bot_slug,
        "timeframe": tf,
        "symbols_source": source,
        "symbols_requested": len(syms),
        "symbols_ok": len(ok),
        "failed": failed,
        "summary": {
            "total_trades": n,
            "wins": len(wins),
            "losses": len(losses),
            "win_rate": round(len(wins) / n * 100, 1) if n else 0.0,
            "avg_trade_pct": round(sum(t["pnl_pct"] for t in all_trades) / n, 2) if n else 0.0,
            "avg_symbol_pnl_pct": round(sum(x["pnl_pct"] for x in per_symbol) / len(per_symbol), 2) if per_symbol else 0.0,
            "profit_factor": round(gw / gl, 2) if gl > 0 else None,
            "worst_symbol_dd_pct": max((x["max_drawdown_pct"] for x in per_symbol), default=0.0),
            "reliable": n >= 30,
        },
        "per_symbol": per_symbol,
        "trades": all_trades,
    }
