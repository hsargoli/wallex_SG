"""API ربات تعقیب بهترین قیمت. پیش‌فرض شبیه‌سازی است."""
from decimal import Decimal
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.core.config import Settings, get_settings
from app.domain.ports.exchange import ExchangePort
from app.presentation.api.deps import get_exchange
from app.services.order_chase.logic import decide
from app.services.order_chase.worker import ChaseConfig, ChaseWorker, manager, validate_market

router = APIRouter(prefix="/order-chase", tags=["Order Chase"])


class CreateChase(BaseModel):
    symbol: str = Field(min_length=3, max_length=20)
    side: Literal["BUY", "SELL"]
    low: Decimal = Field(gt=0)
    high: Decimal = Field(gt=0)
    quantity: Decimal = Field(gt=0)
    dry_run: bool = True
    max_notional: Decimal | None = Field(default=None, gt=0)
    max_moves: int = Field(default=200, ge=1, le=1000)
    enforce_bound: bool = False
    deadline_minutes: int = Field(default=360, ge=1, le=1440)
    interval_sec: int = Field(default=60, ge=30, le=600)


@router.get("/preview")
async def preview(
    symbol: str,
    side: Literal["BUY", "SELL"],
    low: Decimal,
    high: Decimal,
    exchange: ExchangePort = Depends(get_exchange),
):
    """فقط‌خواندنی: دفتر را می‌خواند و می‌گوید ربات الان چه می‌کرد. چیزی ثبت نمی‌کند."""
    if low > high:
        raise HTTPException(400, "کف بازه نباید از سقف بزرگ‌تر باشد")
    sym = symbol.upper()
    try:
        market = await exchange.get_market(sym)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(400, f"نماد نامعتبر: {e}")
    w = ChaseWorker(ChaseConfig(sym, side, low, high, Decimal(1)), exchange, lambda: False, market)
    bids, asks = await w._book()
    bids.sort(key=lambda x: -x[0])
    asks.sort(key=lambda x: x[0])
    d = decide(side, bids, asks, low, high, w._tick())
    return {
        "symbol": sym,
        "best_bid": str(bids[0][0]) if bids else None,
        "best_ask": str(asks[0][0]) if asks else None,
        "bids_top3": [[str(p), str(q)] for p, q in bids[:3]],
        "asks_top3": [[str(p), str(q)] for p, q in asks[:3]],
        "tick": str(w._tick()),
        "step": str(getattr(market, "step_size", None)),
        "min_notional": str(getattr(market, "min_notional", None)),
        "min_quantity": str(getattr(market, "min_quantity", None)),
        "decision": {"action": d.action.value, "price": str(d.price) if d.price else None, "reason": d.reason},
    }


@router.post("", status_code=201)
async def create_chase(
    body: CreateChase,
    exchange: ExchangePort = Depends(get_exchange),
    settings: Settings = Depends(get_settings),
):
    if body.low > body.high:
        raise HTTPException(400, "کف بازه نباید از سقف بزرگ‌تر باشد")
    if not body.dry_run:
        if not settings.can_trade:
            raise HTTPException(403, "معامله واقعی غیرفعال است")
        if body.max_notional is None:
            raise HTTPException(400, "در حالت واقعی سقف ارزش کل (max_notional) الزامی است")
        if body.quantity * body.high > body.max_notional:
            raise HTTPException(400, "مقدار × سقف بازه از max_notional بیشتر است")
    sym = body.symbol.upper()
    try:
        market = await exchange.get_market(sym)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(400, f"نماد نامعتبر: {e}")
    cfg = ChaseConfig(
        symbol=sym, side=body.side, low=body.low, high=body.high, quantity=body.quantity,
        interval_sec=body.interval_sec, dry_run=body.dry_run, max_moves=body.max_moves,
        max_notional=body.max_notional, enforce_bound=body.enforce_bound,
        deadline_sec=body.deadline_minutes * 60,
    )
    err = validate_market(cfg, market)
    if err:
        raise HTTPException(400, err)
    try:
        w = manager.create(cfg, exchange, lambda: get_settings().can_trade, market)
    except ValueError as e:
        raise HTTPException(409, str(e))
    return w.snapshot()


@router.get("")
async def list_chases():
    items = sorted(manager.items.values(), key=lambda w: -w.started_at)
    return {"items": [w.snapshot() for w in items]}


@router.post("/{chase_id}/stop")
async def stop_chase(chase_id: str):
    w = await manager.stop(chase_id)
    if w is None:
        raise HTTPException(404, "تعقیب پیدا نشد")
    return w.snapshot()
