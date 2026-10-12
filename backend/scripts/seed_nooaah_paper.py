"""Seed Nooaah state for UI testing (development only).

⚠️ این اسکریپت state واقعی رو overwrite می‌کنه.
   فقط برای تست UI — نه برای production.

Usage (from ~/wallex/backend):
    uv run python -m scripts.seed_nooaah_paper
"""

from __future__ import annotations

import time
from pathlib import Path

from app.services.bots.nooaah.state import (
    STATE_FILE,
    NooaahClosedTrade,
    NooaahState,
)


def make_trade(
    idx: int,
    symbol: str,
    return_pct: float,
    days_ago: float,
    confidence: int,
) -> NooaahClosedTrade:
    """یه trade فرضی."""
    DAY = 86400
    entry_time = int(time.time() - days_ago * DAY)
    exit_time = entry_time + 3600 * 6  # ۶ ساعت باز
    entry_price = 100_000 * (1 + idx * 0.01)
    exit_price = entry_price * (1 + return_pct / 100)
    capital_used = 500_000.0
    pnl = capital_used * return_pct / 100.0
    return NooaahClosedTrade(
        client_id=f"seed_{idx:03d}_{symbol}",
        symbol=symbol,
        entry_price=entry_price,
        exit_price=exit_price,
        quantity=capital_used / entry_price,
        entry_time=entry_time,
        exit_time=exit_time,
        exit_reason="take_profit" if return_pct > 0 else "stop_loss",
        return_pct=return_pct,
        pnl=round(pnl, 2),
        duration_candles=6,
        confidence=confidence,
        mode="paper-testing",
    )


def main() -> None:
    DAY = 86400
    now = int(time.time())

    trades = [
        # ۱۲ trade با ۶۰٪ WR (۷-۸ برد، ۴-۵ باخت)
        make_trade(1, "BTCTMN",  +2.34, 6.5, 88),
        make_trade(2, "ETHTMN",  +1.12, 6.2, 90),
        make_trade(3, "PUMPTMN", -1.50, 5.8, 87),
        make_trade(4, "USDTTMN", +0.95, 5.3, 92),
        make_trade(5, "TRXTMN",  +1.78, 4.9, 86),
        make_trade(6, "BTCTMN",  -1.20, 4.5, 88),
        make_trade(7, "ETHTMN",  +2.10, 4.0, 91),
        make_trade(8, "PUMPTMN", +3.45, 3.5, 89),
        make_trade(9, "USDTTMN", -0.88, 3.0, 90),
        make_trade(10, "BTCTMN", +1.65, 2.5, 93),
        make_trade(11, "TRXTMN", +0.72, 2.0, 85),
        make_trade(12, "ETHTMN", +2.90, 1.5, 94),
    ]

    state = NooaahState(
        mode="paper-testing",
        capital_total=5_000_000.0,
        capital_available=5_000_000.0 + sum(t.pnl for t in trades),
        capital_in_use=0.0,
        daily_loss_limit_pct=2.0,
        closed_trades=trades,
        paper_started_at=now - 8 * DAY,
        kill_activations_7d=0,
        daily_loss_hits_7d=0,
    )

    state.save(STATE_FILE)
    print(f"✅ Seeded {len(trades)} trades")
    print(f"   paper_started_at: 8 روز قبل")
    print(f"   capital_total: {state.capital_total:,.0f}")
    print(f"   capital_available: {state.capital_available:,.0f}")

    # readiness check
    r = state.readiness_checklist()
    print(f"\n📋 readiness: all_met={r['all_met']}")
    for c in r["conditions"]:
        icon = "✅" if c["met"] else "❌"
        print(f"   {icon} {c['label']}: {c['current']} / {c['target']} {c['unit']}")


if __name__ == "__main__":
    main()
