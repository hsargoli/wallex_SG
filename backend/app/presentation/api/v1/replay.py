"""Historical Replay endpoints."""

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from app.services.historical_replay import replay_bot

router = APIRouter(prefix="/replay", tags=["Historical Replay"])


class ReplayConfigUpdate(BaseModel):
    symbols: list[str] | None = None
    timeframe: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    speed: int | None = Field(None, ge=10, le=10000)
    max_positions: int | None = Field(None, ge=1, le=5)
    ml_threshold: float | None = Field(None, ge=0.0, le=1.0)
    rule_min_score: int | None = Field(None, ge=0, le=10)
    initial_capital: float | None = Field(None, gt=0)


@router.get("/status")
async def get_status():
    """وضعیت فعلی Replay Bot."""
    return replay_bot.get_status()


@router.post("/start")
async def start(request: Request, config: ReplayConfigUpdate | None = None):
    """شروع replay روی داده‌ی تاریخی."""
    exchange = request.app.state.exchange
    cfg = config.model_dump(exclude_none=True) if config else None
    return await replay_bot.start(exchange, config=cfg)


@router.post("/stop")
async def stop():
    """توقف replay."""
    return await replay_bot.stop()


@router.post("/reset")
async def reset():
    """ریست کامل."""
    return replay_bot.reset()
