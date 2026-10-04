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


# ---------- Bot-Specific Budget Schemas ----------


from pydantic import BaseModel, Field


class BotBudgetUpdateRequest(BaseModel):
    """درخواست تخصیص بودجه به یک ربات."""

    allocated: Decimal = Field(..., ge=0, description="مبلغ تخصیصی به این ربات")


class BotBudgetResponse(BaseModel):
    """وضعیت بودجه‌ی یک ربات."""

    slug: str
    allocated: Decimal
    in_use: Decimal
    free: Decimal
    usage_pct: float
    currency: str = "TMN"


class BotBudgetListResponse(BaseModel):
    """لیست بودجه‌ی همه‌ی ربات‌ها."""

    count: int
    items: list[BotBudgetResponse]


class TotalBudgetResponse(BaseModel):
    """وضعیت کلی بودجه (برای صفحه‌ی کیف پول ربات)."""

    total_budget: Decimal
    total_allocated: Decimal
    unallocated: Decimal
    total_in_use: Decimal
    available: Decimal
    allocated_budget: Decimal
    in_use_capital: Decimal
    available_for_trade: Decimal
    currency: str = "TMN"
