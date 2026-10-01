"""Portfolio Allocator — تخصیص سرمایه به ربات‌ها بر اساس رژیم."""

from dataclasses import dataclass

from app.domain.entities.candle import Candle
from app.services.bots.smart_portfolio.config import BotAllocation, SmartPortfolioConfig
from app.services.regime_detector import RegimeResult, detect_regime


@dataclass(slots=True)
class BotSlot:
    """یک اسلات فعال."""

    bot_slug: str
    weight: float  # 0-1
    capital_allocated: float  # به تومان
    reason: str


@dataclass(slots=True)
class AllocationPlan:
    """نتیجه‌ی تخصیص."""

    regime: str
    regime_confidence: int
    regime_reasons: list[str]
    slots: list[BotSlot]
    total_weight: float
    is_safe: bool  # آیا در رژیم مناسب هستیم؟


def allocate(
    candles: list[Candle],
    total_capital: float,
    config: SmartPortfolioConfig,
) -> AllocationPlan:
    """
    تخصیص سرمایه بر اساس رژیم فعلی بازار.
    """
    # ---------- ۱. تشخیص رژیم ----------
    regime_res: RegimeResult = detect_regime(candles)
    regime = (
        regime_res.regime.value if hasattr(regime_res.regime, "value") else str(regime_res.regime)
    )

    # ---------- ۲. پیدا کردن تخصیص ----------
    allocations: list[BotAllocation] = config.regime_map.get(regime, [])

    # اگه رژیم ناشناخته بود → default
    if not allocations:
        if regime == "trending_down":
            # روند نزولی → هیچ رباتی فعال نشه
            return AllocationPlan(
                regime=regime,
                regime_confidence=regime_res.confidence,
                regime_reasons=regime_res.reasons,
                slots=[],
                total_weight=0.0,
                is_safe=False,
            )
        allocations = config.default_allocation

    # ---------- ۳. محدود کردن تعداد ----------
    allocations = allocations[: config.max_concurrent_bots]

    # ---------- ۴. نرمال‌سازی وزن‌ها ----------
    total_w = sum(a.weight for a in allocations)
    if total_w <= 0:
        return AllocationPlan(
            regime=regime,
            regime_confidence=regime_res.confidence,
            regime_reasons=regime_res.reasons,
            slots=[],
            total_weight=0.0,
            is_safe=False,
        )

    # ---------- ۵. ساخت اسلات‌ها ----------
    slots = []
    for alloc in allocations:
        normalized_w = alloc.weight / total_w
        slots.append(
            BotSlot(
                bot_slug=alloc.bot_slug,
                weight=normalized_w,
                capital_allocated=total_capital * normalized_w,
                reason=f"رژیم {regime} (confidence={regime_res.confidence}%)",
            )
        )

    # ---------- ۶. تصمیم نهایی ----------
    # اگه رژیم trending_down یا confidence خیلی پایین → is_safe=False
    is_safe = regime != "trending_down" and regime_res.confidence >= 40

    return AllocationPlan(
        regime=regime,
        regime_confidence=regime_res.confidence,
        regime_reasons=regime_res.reasons,
        slots=slots,
        total_weight=1.0,
        is_safe=is_safe,
    )


def explain_plan(plan: AllocationPlan) -> str:
    """توضیح انسانی از پلن."""
    lines = [
        f"📊 رژیم بازار: {plan.regime}",
        f"   اطمینان: {plan.regime_confidence}%",
        f"   دلایل: {', '.join(plan.regime_reasons[:3])}",
        "",
    ]
    if not plan.slots:
        lines.append("⚠️ هیچ رباتی فعال نمی‌شود (رژیم نامناسب)")
    else:
        lines.append("🤖 ربات‌های فعال:")
        for slot in plan.slots:
            lines.append(
                f"   • {slot.bot_slug:20} "
                f"وزن {slot.weight * 100:>5.1f}%  "
                f"سرمایه {slot.capital_allocated:>10,.0f}"
            )
    return "\n".join(lines)
