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
