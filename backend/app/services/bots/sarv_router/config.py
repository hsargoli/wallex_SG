"""SarvRouterConfig — regime thresholds + capital allocation."""
from dataclasses import dataclass


@dataclass(slots=True)
class SarvRouterConfig:
    """Config برای SarvRouter (Regime-Based Bot Orchestrator)."""

    # ── Regime detection ──
    enable_multi_tf: bool = False  # Phase 1J
    adx_period: int = 14
    ema_period: int = 50
    uptrend_adx_min: float = 25.0
    downtrend_adx_min: float = 25.0
    range_adx_max: float = 20.0
    stability_window: int = 36    # candles regime must be stable
    cooldown_candles: int = 12    # candles after switch
    warmup_candles: int = 100     # min candles for indicators

    # ── Capital allocation (% of total) — must sum to 100 ──
    uptrend_capital_pct: float = 60.0
    range_capital_pct: float = 30.0
    downtrend_capital_pct: float = 0.0
    cash_reserve_pct: float = 10.0

    # ── Bot mapping (None = Cash) ──
    uptrend_bot: str | None = "nooaah"
    range_bot: str | None = "sarvban"
    downtrend_bot: str | None = None

    # ── Risk ──
    daily_loss_limit_pct: float = 2.0
    max_per_bot_pct: float = 60.0
