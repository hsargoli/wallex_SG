"""PaperAdapter — fully local simulation for Paper Mode (no Wallex API needed)."""
import logging
import random
from typing import Optional, List
from app.domain.ports.margin_exchange import (
    MarginExchangePort, MarginPosition, DryRunResult, OrderBookInfo
)

logger = logging.getLogger(__name__)

class PaperAdapter(MarginExchangePort):
    def __init__(self, initial_balance: float = 100_000.0):
        self.balance = initial_balance
        self.positions: list[MarginPosition] = []

    async def get_balance(self) -> float:
        return self.balance

    async def get_order_book(self, market: str) -> OrderBookInfo:
        # Simulate a tight spread
        return OrderBookInfo(spread_pct=0.1, best_bid=21500000000, best_ask=21501000000)

    async def get_positions(self, active: bool = True) -> List[MarginPosition]:
        return [p for p in self.positions if p.state == "open"]

    async def dry_run(self, collateral: str, market: str, open_price: str, risk_coef: str, side: str, stop_loss: Optional[str] = None, take_profit: Optional[str] = None) -> DryRunResult:
        entry = float(open_price)
        # Simulate available liquidity
        return DryRunResult(
            liquidity_price=entry * 2.0 if side == "short" else entry * 0.5,
            call_price=entry * 1.5 if side == "short" else entry * 0.7,
            open_fee=float(collateral) * 0.002,
            trade_fee=float(collateral) * 0.002,
            extend_fee=0.0,
            loan_amount=float(collateral),
            max_age=86400,
            risk_coef=int(risk_coef),
            borrow_fee_pct_24h=0.01
        )

    async def open_position(self, collateral: str, market: str, open_price: str, risk_coef: str, side: str, stop_loss: Optional[str] = None, take_profit: Optional[str] = None) -> MarginPosition:
        # This should not be called in paper mode (executor handles it), but just in case
        raise NotImplementedError("Use executor._make_paper_position")

    async def close_position(self, position_id: str, price: str) -> MarginPosition:
        raise NotImplementedError("Paper close not implemented yet")
