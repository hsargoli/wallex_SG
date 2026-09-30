"""Scalping Bot endpoint."""

import asyncio

from fastapi import APIRouter, HTTPException, status

from app.application.use_cases.get_candles import GetCandlesUseCase
from app.presentation.api.deps import ExchangeDep
from app.services.scalping_backtest import run_scalping_backtest

router = APIRouter(prefix="/scalping", tags=["Scalping"])


@router.get("/backtest")
async def backtest(
    exchange: ExchangeDep,
    symbols: str = "BTCTMN,ETHTMN,XRPTMN,DOGETMN,SOLTMN",
    tf: str = "15m",
    limit: int = 800,
    initial_capital: float = 300_000,
    max_positions: int = 2,
):
    """اجرای backtest اسکالپینگ روی چند مارکت."""
    sym_list = [s.strip().upper() for s in symbols.split(",") if s.strip()]
    use_case = GetCandlesUseCase(exchange=exchange)

    async def fetch(sym: str):
        try:
            return sym, await use_case.execute(symbol=sym, timeframe=tf, limit=limit)
        except Exception:
            return sym, []

    results = await asyncio.gather(*[fetch(s) for s in sym_list])
    markets_data = {sym: candles for sym, candles in results if candles}

    if not markets_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="داده‌ای یافت نشد",
        )

    result = run_scalping_backtest(
        markets_data=markets_data,
        initial_capital=initial_capital,
        max_positions=max_positions,
    )

    recent = [
        {
            "symbol": t.symbol,
            "entry_time": t.entry_time,
            "exit_time": t.exit_time,
            "entry_price": str(t.entry_price),
            "exit_price": str(t.exit_price),
            "pnl_pct": round(t.pnl_pct, 3),
            "pnl_tmn": round(t.pnl_tmn, 1),
            "exit_reason": t.exit_reason,
            "duration_candles": t.duration_candles,
        }
        for t in result.trades[-30:]
    ]

    return {
        "symbols": list(markets_data.keys()),
        "timeframe": tf,
        "candles_per_symbol": {s: len(c) for s, c in markets_data.items()},
        "initial_capital": result.initial_capital,
        "final_capital": round(result.final_capital, 1),
        "total_trades": result.total_trades,
        "wins": result.wins,
        "losses": result.losses,
        "win_rate": round(result.win_rate, 2),
        "total_return_pct": round(result.total_return_pct, 2),
        "max_drawdown_pct": round(result.max_drawdown_pct, 2),
        "avg_win_pct": round(result.avg_win_pct, 3),
        "avg_loss_pct": round(result.avg_loss_pct, 3),
        "equity_curve": [round(e, 1) for e in result.equity_curve],
        "recent_trades": recent,
    }
