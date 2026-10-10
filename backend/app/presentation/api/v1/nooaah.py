"""Nooaah endpoints — status زنده + backtest."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.application.use_cases.get_candles import GetCandlesUseCase
from app.presentation.api.deps import ExchangeDep
from app.services.bots.nooaah.backtest import run_nooaah_backtest
from app.services.bots.nooaah.bot import NooaahBot
from app.services.bots.nooaah.config import NooaahConfig

router = APIRouter(prefix="/nooaah", tags=["Nooaah"])


# ---------- Schemas ----------

class ProposalOut(BaseModel):
    symbol: str
    action: str
    entry: float
    take_profit: float
    stop_loss: float
    confidence: int
    regime: str
    reason: str


class StatusOut(BaseModel):
    symbols_analyzed: list[str]
    duration_seconds: float
    proposal: ProposalOut | None
    error: str | None = None


class TradeOut(BaseModel):
    entry_price: str
    exit_price: str
    side: str
    return_pct: float
    exit_reason: str
    confidence: int
    duration_candles: int


class BacktestOut(BaseModel):
    symbols: list[str]
    candles_analyzed: int
    signals_generated: int
    total_trades: int
    wins: int
    losses: int
    win_rate: float
    total_return_pct: float
    max_drawdown_pct: float
    profit_factor: float
    sharpe_ratio: float
    avg_duration_candles: float
    equity_curve_full: list[float]
    buy_hold_curve: list[float]
    recent_trades: list[TradeOut]


# ---------- Endpoints ----------

@router.get("/status", response_model=StatusOut)
async def status_now(exchange: ExchangeDep, top: int = 5) -> StatusOut:
    """اجرای یک چرخه‌ی تحلیل + تصمیم زنده."""
    bot = NooaahBot(exchange=exchange, config=NooaahConfig(top_n=top))
    result = await bot.run_once()
    proposal = None
    if result.proposal is not None:
        p = result.proposal
        proposal = ProposalOut(
            symbol=p.symbol,
            action=p.action,
            entry=round(p.entry, 2),
            take_profit=round(p.take_profit, 2),
            stop_loss=round(p.stop_loss, 2),
            confidence=p.confidence,
            regime=p.regime,
            reason=p.reason,
        )
    return StatusOut(
        symbols_analyzed=result.symbols_analyzed,
        duration_seconds=round(result.duration_seconds, 2),
        proposal=proposal,
        error=result.error,
    )


@router.get("/backtest", response_model=BacktestOut)
async def backtest(
    exchange: ExchangeDep,
    top: int = 5,
    limit: int = 500,
) -> BacktestOut:
    """اجرای backtest روی top نمادهای پرحجم."""
    cfg = NooaahConfig(top_n=top)
    bot = NooaahBot(exchange=exchange, config=cfg)
    symbols = await bot.pick_top_symbols(top)
    if not symbols:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="no markets returned from Wallex",
        )

    uc = GetCandlesUseCase(exchange=exchange)
    candles_by_symbol = {}
    for sym in symbols:
        try:
            c = await uc.execute(symbol=sym, timeframe="1h", limit=limit)
            if c:
                candles_by_symbol[sym] = c
        except Exception:
            continue

    if not candles_by_symbol:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="no candles fetched",
        )

    try:
        stats = run_nooaah_backtest(candles_by_symbol, cfg)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e
    recent = [
        TradeOut(
            entry_price=str(t.entry_price),
            exit_price=str(t.exit_price),
            side=t.side,
            return_pct=round(t.return_pct, 3),
            exit_reason=t.exit_reason,
            confidence=t.confidence,
            duration_candles=t.duration_candles,
        )
        for t in stats.trades[-5:]
    ]
    return BacktestOut(
        symbols=list(candles_by_symbol.keys()),
        candles_analyzed=stats.candles_analyzed,
        signals_generated=stats.signals_generated,
        total_trades=stats.total_trades,
        wins=stats.wins,
        losses=stats.losses,
        win_rate=round(stats.win_rate, 2),
        total_return_pct=round(stats.total_return_pct, 2),
        max_drawdown_pct=round(stats.max_drawdown_pct, 2),
        profit_factor=round(stats.profit_factor, 2),
        sharpe_ratio=round(stats.sharpe_ratio, 3),
        avg_duration_candles=round(stats.avg_duration_candles, 1),
        equity_curve_full=stats.equity_curve_full,
        buy_hold_curve=stats.buy_hold_curve,
        recent_trades=recent,
    )
