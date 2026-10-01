"""Paper Trading v2 — با Dispatcher."""

from fastapi import APIRouter, Request

from app.services.paper_trader_v2 import paper_trader_v2

router = APIRouter(prefix="/paper-v2", tags=["Paper V2"])


@router.get("/status")
async def get_status():
    return paper_trader_v2.get_status()


@router.post("/start")
async def start(request: Request):
    exchange = request.app.state.exchange
    return await paper_trader_v2.start(exchange)


@router.post("/stop")
async def stop():
    return await paper_trader_v2.stop()


@router.post("/reset")
async def reset():
    return paper_trader_v2.reset()
