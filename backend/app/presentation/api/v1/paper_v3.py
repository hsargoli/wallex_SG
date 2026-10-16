"""Paper Trading v3 — موتور حرفه‌ای."""

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel

from app.infrastructure.paper_trading.engine import PaperEngine

router = APIRouter(prefix="/paper-v3", tags=["Paper V3"])


class StartRequest(BaseModel):
    bot_slug: str = "scalp_master"
    symbols: list[str] = ["NEARTMN"]
    timeframe: str = "1h"
    initial_capital: float = 1000.0
    check_interval_sec: int = 180
    position_size_pct: float = 50.0


# State در app.state
def get_engine(request: Request) -> PaperEngine | None:
    return getattr(request.app.state, "paper_v3_engine", None)


@router.get("/status")
async def get_status(request: Request):
    """وضعیت Paper Trading."""
    engine = get_engine(request)
    if engine is None:
        return {
            "is_running": False,
            "initial_capital": 1000.0,
            "capital": 1000.0,
            "peak_capital": 1000.0,
            "max_drawdown_pct": 0.0,
            "total_trades": 0,
            "wins": 0,
            "losses": 0,
            "total_pnl": 0.0,
            "total_pnl_pct": 0.0,
            "win_rate": 0.0,
            "open_positions": [],
            "recent_trades": [],
            "equity_curve": [],
            "started_at": 0,
            "last_check_at": 0,
            "check_count": 0,
            "config": {},
        }
    return engine.get_status()


@router.get("/live")
async def get_live(request: Request):
    """State + قیمت لحظه‌ای (PnL شناور)."""
    engine = get_engine(request)
    if engine is None:
        return {
            "is_running": False,
            "equity": 0.0,
            "total_pnl": 0.0,
            "total_pnl_pct": 0.0,
            "open_positions": [],
        }
    await engine.refresh_prices()
    return engine.get_status()


@router.post("/start")
async def start(request: Request, payload: StartRequest):
    """شروع Paper Trading."""
    # اگه engine در حال اجرا هست، اول متوقف کن
    old = get_engine(request)
    if old is not None and old.state.is_running:
        await old.stop()

    exchange = request.app.state.exchange

    engine = PaperEngine(
        exchange=exchange,
        bot_slug=payload.bot_slug,
        symbols=payload.symbols,
        timeframe=payload.timeframe,
        initial_capital=payload.initial_capital,
        check_interval_sec=payload.check_interval_sec,
        position_size_pct=payload.position_size_pct,
    )

    request.app.state.paper_v3_engine = engine

    result = await engine.start()
    return result


@router.post("/stop")
async def stop(request: Request):
    """توقف."""
    engine = get_engine(request)
    if engine is None:
        return {"status": "stopped"}
    return await engine.stop()


@router.post("/reset")
async def reset(request: Request):
    """ریست."""
    engine = get_engine(request)
    if engine is None:
        # اگه engine نیست، state خالی برگردون
        from app.infrastructure.paper_trading.repository import PaperRepository
        from app.infrastructure.paper_trading.state import PaperState
        repo = PaperRepository()
        await repo.save(PaperState())
        return {"status": "reset"}
    return await engine.reset()
