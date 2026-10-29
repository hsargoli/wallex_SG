"""CapitalAllocator — decide how much capital each bot gets per regime."""
from typing import Any

from app.services.bots.sarv_router.config import SarvRouterConfig
from app.services.bots.sarv_router.regime import Regime


def allocate_capital(
    total: float,
    regime: Regime,
    config: SarvRouterConfig,
) -> dict[str, Any]:
    """Allocate total capital based on regime.

    Returns:
        {
          "regime": str,
          "active_bots": [slug, ...],
          "allocations": {slug: amount},
          "cash": amount,
        }
    Invariant: sum(allocations.values()) + cash == total
    """
    if total < 0:
        raise ValueError(f"total capital must be >= 0, got {total}")

    # Unknown/Downtrend → 100% cash (per ADR)
    if regime in (Regime.DOWNTREND, Regime.UNKNOWN):
        return {
            "regime": str(regime.value if hasattr(regime, "value") else regime),
            "active_bots": [],
            "allocations": {},
            "cash": float(total),
        }

    # Determine bot + target pct for this regime
    if regime == Regime.UPTREND:
        bot_slug = config.uptrend_bot
        target_pct = config.uptrend_capital_pct
    elif regime == Regime.RANGE:
        bot_slug = config.range_bot
        target_pct = config.range_capital_pct
    else:
        # Defensive — unexpected regime
        return {
            "regime": str(regime.value if hasattr(regime, "value") else regime),
            "active_bots": [],
            "allocations": {},
            "cash": float(total),
        }

    if bot_slug is None or target_pct <= 0:
        return {
            "regime": str(regime.value if hasattr(regime, "value") else regime),
            "active_bots": [],
            "allocations": {},
            "cash": float(total),
        }

    # Enforce max_per_bot cap
    effective_pct = min(target_pct, config.max_per_bot_pct)
    allocation = round(total * effective_pct / 100.0, 2)
    cash = round(total - allocation, 2)

    return {
        "regime": str(regime.value if hasattr(regime, "value") else regime),
        "active_bots": [bot_slug],
        "allocations": {bot_slug: allocation},
        "cash": cash,
    }
