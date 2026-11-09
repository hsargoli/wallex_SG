"""Alternatives — generate adjacent regime scenarios (ADR-0044)."""
from app.services.bots.sarv_router.regime import Regime
from app.services.bots.sarv_router.capital_allocator import allocate_capital


def get_adjacent_regimes(regime: Regime) -> list[Regime]:
    if regime == Regime.UPTREND:
        return [Regime.RANGE]
    elif regime == Regime.RANGE:
        return [Regime.UPTREND, Regime.DOWNTREND]
    elif regime == Regime.DOWNTREND:
        return [Regime.RANGE]
    return []


def generate_alternatives(current_regime: Regime, total_capital: float, config) -> list[dict]:
    adjacent = get_adjacent_regimes(current_regime)
    alts = []
    for alt_regime in adjacent:
        alloc = allocate_capital(total_capital, alt_regime, config)
        alts.append({
            "regime": alt_regime.value,
            "allocations": alloc["allocations"],
            "active_bots": alloc["active_bots"],
            "cash": alloc["cash"],
        })
    return alts
