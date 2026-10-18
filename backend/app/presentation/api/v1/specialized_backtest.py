"""Specialized Backtest Endpoints for Bear Hunter and Nooaah."""
from fastapi import APIRouter, HTTPException, Query
from decimal import Decimal
from pydantic import BaseModel
from typing import Optional

from app.services.bots.bear_hunter.backtest import run_backtest as run_bear_bt
from app.services.bots.bear_hunter.paths import USERS_DIR

router = APIRouter(prefix="/specialized-backtest", tags=["Specialized Backtest"])

class BearHunterResult(BaseModel):
    total_pnl_pct: float
    total_trades: int
    wins: int
    losses: int
    max_drawdown_pct: float

@router.get("/bear_hunter/{symbol}")
async def backtest_bear_hunter(
    symbol: str,
    start_date: str = Query(...),
    end_date: str = Query(...),
    direction: str = Query("bearish"),
    initial_capital: float = Query(5000000.0),
):
    """Run Bear Hunter's native backtest engine."""
    try:
        # We only have data for BTC, ETH, SOL mapped
        symbol_map = {"BTCTMN": "BTCUSDT", "ETHTMN": "ETHUSDT", "SOLTMN": "SOLUSDT"}
        file_symbol = symbol_map.get(symbol, "BTCUSDT")
        
        from app.services.bots.bear_hunter.paths import DATA_DIR
        csv_path = DATA_DIR / "historical" / f"{file_symbol}_1h.csv"
        
        if not csv_path.exists():
            raise HTTPException(404, detail=f"Historical data not found for {symbol}")
            
        res = run_bear_bt(
            csv_path=str(csv_path),
            initial_capital=Decimal(str(initial_capital)),
            human_direction=direction,
            start_date=start_date,
            end_date=end_date
        )
        
        if "error" in res:
            raise HTTPException(400, detail=res["error"])
            
        return {
            "bot": "bear_hunter",
            "symbol": symbol,
            "result": {
                "total_pnl_pct": res["total_pnl_pct"],
                "total_trades": res["total_trades"],
                "wins": res["wins"],
                "losses": res["losses"],
                "avg_win": res.get("avg_win", 0),
                "avg_loss": res.get("avg_loss", 0),
                "exit_counts": res.get("exit_counts", {})
            }
        }
    except Exception as e:
        raise HTTPException(500, detail=str(e))

@router.get("/nooaah/{symbol}")
async def backtest_nooaah(
    symbol: str,
    start_date: str = Query(...),
    end_date: str = Query(...),
    initial_capital: float = Query(5000000.0),
):
    """Run Nooaah's native backtest engine."""
    try:
        # Placeholder for Nooaah integration
        # Since Nooaah has its own ML/Regime logic, we'll need to adapt its run_backtest
        # For now, return a friendly message
        raise HTTPException(501, detail="Nooaah specialized backtest is under construction.")
    except Exception as e:
        raise HTTPException(500, detail=str(e))
