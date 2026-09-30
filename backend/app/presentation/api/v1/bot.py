"""Bot management endpoints (budget, etc.)."""

from fastapi import APIRouter, HTTPException, status

from app.domain.models.budget import BudgetResponse, BudgetUpdateRequest
from app.services.budget_service import budget_service

router = APIRouter(prefix="/bot", tags=["Bot Management"])


@router.get("/budget", response_model=BudgetResponse)
def get_bot_budget():
    """دریافت وضعیت بودجه فعلی ربات."""
    return budget_service.get_status()


@router.post("/budget", response_model=BudgetResponse)
def update_bot_budget(payload: BudgetUpdateRequest):
    """تعیین یا به‌روزرسانی سقف بودجه ربات."""
    try:
        budget_service.set_budget(payload.allocated_budget)
        return budget_service.get_status()
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
