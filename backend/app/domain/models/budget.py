from decimal import Decimal

from pydantic import BaseModel, Field


class BudgetUpdateRequest(BaseModel):
    # Maximum budget in TMN allocated to this bot instance
    allocated_budget: Decimal = Field(
        ...,
        gt=0,
        description="Total budget allocated to the bot in TMN (must be > 0)",
        examples=[100000.0],
    )


class BudgetResponse(BaseModel):
    allocated_budget: Decimal = Field(..., description="Total budget allocated to the bot")
    in_use_capital: Decimal = Field(
        ..., description="Capital currently locked in active orders/positions"
    )
    available_for_trade: Decimal = Field(
        ..., description="Remaining free budget available for new trades"
    )
    currency: str = Field(default="TMN", description="Base operational currency")
