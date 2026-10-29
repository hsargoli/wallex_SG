"""Backtest adapter — simulate SarvRouter over historical candles."""
from app.domain.entities.candle import Candle
from app.services.bots.sarv_router.bot import SarvRouter


def run_sarv_backtest(router, user_id, candles):
    total_ticks = 0
    switches = 0
    kill_events = 0
    regime_sequence: list[str] = []
    cash_trace: list[float] = []

    for i in range(len(candles)):
        window = candles[: i + 1]
        result = router.tick(user_id, window, now_idx=i)
        total_ticks += 1
        action = result.get("action", "")

        if action == "switched":
            switches += 1
        if action in ("kill_switch_active", "daily_loss_kill"):
            kill_events += 1

        st = router.store.load(user_id)
        regime_sequence.append(st.current_regime)
        cash_trace.append(st.cash)

    st_final = router.store.load(user_id)
    return {
        "total_ticks": total_ticks,
        "switches": switches,
        "kill_events": kill_events,
        "final_regime": st_final.current_regime,
        "final_active_bots": list(st_final.active_bots),
        "final_allocations": dict(st_final.allocations),
        "final_cash": st_final.cash,
        "regime_sequence": regime_sequence,
        "cash_trace": cash_trace,
    }
