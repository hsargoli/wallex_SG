"""Paper Trading endpoints — کنترل ربات مجازی."""

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from app.services.paper_trader import paper_trader

router = APIRouter(prefix="/paper", tags=["Paper Trading"])


class ConfigUpdate(BaseModel):
    symbols: list[str] | None = None
    timeframe: str | None = None
    check_interval_sec: int | None = Field(None, ge=10, le=3600)
    max_positions: int | None = Field(None, ge=1, le=5)
    ml_threshold: float | None = Field(None, ge=0.0, le=1.0)
    rule_min_score: int | None = Field(None, ge=0, le=10)
    initial_capital: float | None = Field(None, gt=0)


@router.get("/status")
async def get_status():
    """وضعیت فعلی ربات Paper Trading."""
    return paper_trader.get_status()


@router.post("/start")
async def start(request: Request):
    """شروع ربات."""
    exchange = request.app.state.exchange
    result = await paper_trader.start(exchange)
    return result


@router.post("/stop")
async def stop():
    """توقف ربات."""
    return await paper_trader.stop()


@router.post("/reset")
async def reset(payload: ConfigUpdate | None = None):
    """ریست کامل state (با تنظیمات اختیاری)."""
    if payload:
        if payload.symbols:
            paper_trader.config.symbols = payload.symbols
        if payload.timeframe:
            paper_trader.config.timeframe = payload.timeframe
        if payload.check_interval_sec:
            paper_trader.config.check_interval_sec = payload.check_interval_sec
        if payload.max_positions:
            paper_trader.config.max_positions = payload.max_positions
        if payload.ml_threshold is not None:
            paper_trader.config.ml_threshold = payload.ml_threshold
        if payload.rule_min_score is not None:
            paper_trader.config.rule_min_score = payload.rule_min_score
        if payload.initial_capital:
            paper_trader.state.initial_capital = payload.initial_capital
            paper_trader.state.capital = payload.initial_capital
            paper_trader.state.peak_capital = payload.initial_capital

    return paper_trader.reset()


@router.post("/run-once")
async def run_once(request: Request):
    """یک بار چک کردن (برای تست سریع)."""
    exchange = request.app.state.exchange
    if paper_trader._exchange is None:
        paper_trader._exchange = exchange

    if paper_trader._model is None:
        paper_trader._load_model()

    await paper_trader._check_exits()
    await paper_trader._check_entries()
    paper_trader.save_state()

    return paper_trader.get_status()
