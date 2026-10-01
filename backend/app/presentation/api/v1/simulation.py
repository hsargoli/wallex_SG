from fastapi import APIRouter
from app.services.simulator_engine import Simulator
from app.domain.strategy import SimpleTrendStrategy
from app.infrastructure.wallex_repo import WallexMarketData

router = APIRouter()

@router.post("/run")
async def run_simulation(start_date: str, end_date: str):
    strategy = SimpleTrendStrategy()
    repo = WallexMarketData()
    sim = Simulator(strategy=strategy, repo=repo)
    result = sim.run("BTCUSDT", start_date, end_date)
    return {"status": "success", "pnl_report": result}
