from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from decimal import Decimal
from typing import Optional, List

@dataclass(frozen=True)
class MarginPosition:
    position_id: str
    market: str
    side: str
    collateral: float
    entry_price: float
    current_price: float
    liquidation_price: float
    call_price: Optional[float]
    risk_coef: int
    profit_percentage: float
    loan_amount: float
    interest: float
    stop_loss: Optional[float]
    take_profit: Optional[float]
    state: str
    extend_time: int

@dataclass(frozen=True)
class DryRunResult:
    liquidity_price: float
    call_price: float
    open_fee: float
    trade_fee: float
    extend_fee: float
    loan_amount: float
    max_age: int
    risk_coef: int
    borrow_fee_pct_24h: float = 0.0

@dataclass(frozen=True)
class OrderBookInfo:
    spread_pct: float
    best_bid: float
    best_ask: float


class DryRunReason(str, Enum):
    """دلیل شکست dry_run — برای اینکه pre_flight بتونه تصمیم درست بگیره."""
    NO_LIQUIDITY = "no_liquidity"         # ظرفیت مارجین تمام شده
    INVALID_PAYLOAD = "invalid_payload"   # 400 با پیام دیگه
    UNAUTHORIZED = "unauthorized"         # 401/403
    UNKNOWN = "unknown"


class DryRunError(Exception):
    """خطای typed برای dry_run — pre_flight بر اساس reason تصمیم می‌گیره."""
    def __init__(self, reason: DryRunReason, raw_message: str):
        self.reason = reason
        self.raw_message = raw_message
        super().__init__(f"DryRunError({reason}): {raw_message}")


class MarginExchangePort(ABC):
    @abstractmethod
    async def dry_run(self, collateral: str, market: str, open_price: str, risk_coef: str, side: str, stop_loss: Optional[str] = None, take_profit: Optional[str] = None) -> DryRunResult:
        pass

    @abstractmethod
    async def open_position(self, collateral: str, market: str, open_price: str, risk_coef: str, side: str, stop_loss: Optional[str] = None, take_profit: Optional[str] = None) -> MarginPosition:
        pass

    @abstractmethod
    async def get_positions(self, active: bool = True) -> List[MarginPosition]:
        pass

    @abstractmethod
    async def close_position(self, position_id: str, price: str) -> MarginPosition:
        pass

    @abstractmethod
    async def get_balance(self) -> float:
        pass

    @abstractmethod
    async def get_order_book(self, market: str) -> OrderBookInfo:
        pass
