"""Nooaah endpoints — status زنده + backtest."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.application.use_cases.get_candles import GetCandlesUseCase
from app.presentation.api.deps import ExchangeDep
from app.services.bots.nooaah.backtest import run_nooaah_backtest
from app.services.bots.nooaah.bot import NooaahBot
from app.services.bots.nooaah.config import NooaahConfig
from app.services.bots.nooaah.scheduler import get_scheduler
from app.services.bots.nooaah.state import NooaahState

router = APIRouter(prefix="/nooaah", tags=["Nooaah"])


# ---------- Schemas ----------

class NooaahConfigOut(BaseModel):
    mode: str
    capital_total: float
    capital_available: float
    capital_in_use: float
    daily_loss_limit_pct: float
    daily_pnl_pct: float
    daily_loss_hit: bool
    killed: bool
    open_positions_count: int
    closed_trades_count: int
    last_run: int
    scheduler_running: bool
    scheduler_last_status: str | None
    # ADR-0011
    live_stage: int
    consecutive_losses: int
    pause_reason: str
    activated_live_at: int
    paper_started_at: int


class NooaahConfigIn(BaseModel):
    capital_total: float | None = None
    daily_loss_limit_pct: float | None = None


class ReadinessCondition(BaseModel):
    key: str
    label: str
    current: float
    target: float
    unit: str
    met: bool


class ReadinessOut(BaseModel):
    mode: str
    all_met: bool
    conditions: list[ReadinessCondition]
    days_in_paper: int
    recent_trades_count: int
    recent_win_rate: float
    recent_return: float


class ActivateIn(BaseModel):
    confirmation_phrase: str


class DraftOut(BaseModel):
    draft: dict
    defaults: dict
    merged: dict
    step_completed: dict  # کدوم stepها کاملن


class ProposalOut(BaseModel):
    symbol: str
    action: str
    entry: float
    take_profit: float
    stop_loss: float
    confidence: int
    regime: str
    reason: str


class StatusOut(BaseModel):
    symbols_analyzed: list[str]
    duration_seconds: float
    proposal: ProposalOut | None
    error: str | None = None


class TradeOut(BaseModel):
    entry_price: str
    exit_price: str
    side: str
    return_pct: float
    exit_reason: str
    confidence: int
    duration_candles: int


class BacktestOut(BaseModel):
    symbols: list[str]
    candles_analyzed: int
    signals_generated: int
    total_trades: int
    wins: int
    losses: int
    win_rate: float
    total_return_pct: float
    max_drawdown_pct: float
    profit_factor: float
    sharpe_ratio: float
    avg_duration_candles: float
    equity_curve_full: list[float]
    buy_hold_curve: list[float]
    recent_trades: list[TradeOut]


# ---------- Endpoints ----------

@router.get("/config", response_model=NooaahConfigOut)
async def get_nooaah_config() -> NooaahConfigOut:
    """وضعیت config فعلی Nooaah."""
    state = NooaahState.load()
    sched = get_scheduler()
    return NooaahConfigOut(
        mode=state.mode,
        capital_total=state.capital_total,
        capital_available=state.capital_available,
        capital_in_use=state.capital_in_use,
        daily_loss_limit_pct=state.daily_loss_limit_pct,
        daily_pnl_pct=state.daily_pnl_pct,
        daily_loss_hit=state.daily_loss_hit,
        killed=state.killed,
        open_positions_count=len(state.open_positions),
        closed_trades_count=len(state.closed_trades),
        last_run=state.last_run,
        scheduler_running=sched.running if sched else False,
        scheduler_last_status=(
            sched.last_result.get("status") if sched and sched.last_result else None
        ),
        live_stage=state.live_stage,
        consecutive_losses=state.consecutive_losses,
        pause_reason=state.pause_reason,
        activated_live_at=state.activated_live_at,
        paper_started_at=state.paper_started_at,
    )


@router.post("/config", response_model=NooaahConfigOut)
async def update_nooaah_config(body: NooaahConfigIn) -> NooaahConfigOut:
    """تغییر config — capital, mode, daily limit."""
    state = NooaahState.load()

    if body.capital_total is not None:
        if body.capital_total < 0:
            raise HTTPException(400, "capital_total must be >= 0")
        delta = body.capital_total - state.capital_total
        state.capital_total = body.capital_total
        state.capital_available = max(0, state.capital_available + delta)

    if body.daily_loss_limit_pct is not None:
        if body.daily_loss_limit_pct < 0 or body.daily_loss_limit_pct > 100:
            raise HTTPException(400, "daily_loss_limit_pct must be 0-100")
        state.daily_loss_limit_pct = body.daily_loss_limit_pct

    state.save()
    return await get_nooaah_config()


@router.post("/kill", response_model=NooaahConfigOut)
async def kill_nooaah() -> NooaahConfigOut:
    """kill-switch: قفل فوری. نیاز به /resume برای ادامه."""
    import time as _time
    state = NooaahState.load()
    state.killed = True
    state.killed_at = int(_time.time())
    state.kill_activations_7d += 1
    # اگه در live بود → live-paused
    if state.mode == "live-active":
        state.mode = "live-paused"
        state.pause_reason = "kill-switch توسط کاربر"
    state.save()
    return await get_nooaah_config()


@router.post("/resume", response_model=NooaahConfigOut)
async def resume_nooaah() -> NooaahConfigOut:
    """برداشتن kill-switch / live-paused."""
    state = NooaahState.load()
    state.killed = False
    state.killed_at = 0
    state.daily_loss_hit = False
    state.daily_pnl_pct = 0.0
    # اگه live-paused بود → برگرد به live-active
    if state.mode == "live-paused":
        state.mode = "live-active"
        state.pause_reason = ""
        state.consecutive_losses = 0
    state.save()
    return await get_nooaah_config()


# ---------- Live Activation (ADR-0011) ----------

CONFIRMATION_PHRASE = "با مسئولیت خودم"


@router.get("/readiness", response_model=ReadinessOut)
async def get_readiness() -> ReadinessOut:
    """چک‌لیست شرایط برای عبور از paper به ready-for-live."""
    state = NooaahState.load()
    r = state.readiness_checklist()
    return ReadinessOut(
        mode=state.mode,
        all_met=r["all_met"],
        conditions=[
            ReadinessCondition(**c) for c in r["conditions"]
        ],
        days_in_paper=r["days_in_paper"],
        recent_trades_count=r["recent_trades_count"],
        recent_win_rate=r["recent_win_rate"],
        recent_return=r["recent_return"],
    )


def _compute_steps_completed(draft: dict, defaults: dict) -> dict:
    """کدوم از ۶ مرحله توسط کاربر پر شده؟

    چک می‌کنیم k in draft (نه merged) — یعنی کاربر خودش مقدار داده.
    """
    return {
        "step2_strategy": all(
            k in draft for k in ("min_confidence", "confirmation_candles",
                                  "tp_atr_mult", "sl_atr_mult", "volume_z_min")
        ),
        "step3_position": all(
            k in draft for k in ("max_concurrent_positions", "top_n")
        ),
        "step4_capital": draft.get("capital_total", 0) > 0,
        "step5_risk": "daily_loss_limit_pct" in draft,
    }


@router.get("/live/draft", response_model=DraftOut)
async def get_live_draft() -> DraftOut:
    """draft فعلی + پیش‌فرض‌ها."""
    state = NooaahState.load()
    defaults = dict(NooaahState.DEFAULT_RUNTIME_CONFIG)
    merged = state.finalize_draft()
    return DraftOut(
        draft=state.draft_config,
        defaults=defaults,
        merged=merged,
        step_completed=_compute_steps_completed(state.draft_config, defaults),
    )


@router.put("/live/draft", response_model=DraftOut)
async def update_live_draft(body: dict) -> DraftOut:
    """ذخیره‌ی یه مرحله از draft (merge با قبلی)."""
    state = NooaahState.load()
    # merge با draft قبلی (partial save)
    for k, v in body.items():
        state.draft_config[k] = v
    state.save()
    defaults = dict(NooaahState.DEFAULT_RUNTIME_CONFIG)
    merged = state.finalize_draft()
    return DraftOut(
        draft=state.draft_config,
        defaults=defaults,
        merged=merged,
        step_completed=_compute_steps_completed(state.draft_config, defaults),
    )


@router.delete("/live/draft", response_model=DraftOut)
async def clear_live_draft() -> DraftOut:
    """پاک کردن draft."""
    state = NooaahState.load()
    state.draft_config = {}
    state.save()
    defaults = dict(NooaahState.DEFAULT_RUNTIME_CONFIG)
    return DraftOut(
        draft={},
        defaults=defaults,
        merged=defaults,
        step_completed=_compute_steps_completed({}, defaults),
    )


@router.post("/live/activate", response_model=NooaahConfigOut)
async def activate_live(body: ActivateIn) -> NooaahConfigOut:
    """فعال‌سازی live. نیاز: شرایط آماده + عبارت تأیید."""
    import time as _time
    state = NooaahState.load()

    # چک state
    if state.mode == "live-active":
        raise HTTPException(400, "already live")
    if state.mode == "live-paused":
        raise HTTPException(400, "paused — use /resume instead")
    if state.mode != "paper-testing" and state.mode != "ready-for-live":
        raise HTTPException(400, f"invalid mode for activation: {state.mode}")

    # چک عبارت
    if body.confirmation_phrase.strip() != CONFIRMATION_PHRASE:
        raise HTTPException(
            400,
            f"عبارت تأیید اشتباه. باید بنویسی: «{CONFIRMATION_PHRASE}»",
        )

    # چک شرایط
    r = state.readiness_checklist()
    if not r["all_met"]:
        unmet = [c["label"] for c in r["conditions"] if not c["met"]]
        raise HTTPException(
            400,
            "شرایط آماده نیست: " + "، ".join(unmet),
        )

    # نهایی‌سازی draft → runtime_config
    final_config = state.finalize_draft()

    # اعمال سرمایه + daily limit
    state.capital_total = float(final_config.get("capital_total", state.capital_total))
    state.capital_available = state.capital_total
    state.daily_loss_limit_pct = float(
        final_config.get("daily_loss_limit_pct", state.daily_loss_limit_pct)
    )
    state.runtime_config = final_config

    # انتقال
    state.mode = "live-active"
    state.activated_live_at = int(_time.time())
    state.live_stage = 1
    state.pause_reason = ""
    state.consecutive_losses = 0
    state.draft_config = {}  # پاک‌سازی draft بعد از activate
    state.save()
    return await get_nooaah_config()


@router.post("/live/pause", response_model=NooaahConfigOut)
async def pause_live(reason: str = "auto") -> NooaahConfigOut:
    """توقف live — یا auto یا دستی. نیاز به /resume."""
    state = NooaahState.load()
    if state.mode != "live-active":
        raise HTTPException(400, f"not live-active (mode={state.mode})")
    state.mode = "live-paused"
    state.pause_reason = reason
    state.save()
    return await get_nooaah_config()


@router.post("/live/stage/advance", response_model=NooaahConfigOut)
async def advance_stage() -> NooaahConfigOut:
    """ارتقای stage (1 → 2 → 3) بر اساس شرایط."""
    state = NooaahState.load()
    if state.mode != "live-active":
        raise HTTPException(400, "not live-active")

    # شمارش tradeهای live
    live_trades = [t for t in state.closed_trades if t.mode == "live-active" or t.mode == "live"]
    win_count = len([t for t in live_trades if t.return_pct > 0])

    if state.live_stage == 1 and win_count < 5:
        raise HTTPException(400, f"need 5 winning live trades (have {win_count})")
    if state.live_stage == 2 and win_count < 10:
        raise HTTPException(400, f"need 10 winning live trades (have {win_count})")
    if state.live_stage >= 3:
        raise HTTPException(400, "already at full stage")

    state.live_stage += 1
    state.save()
    return await get_nooaah_config()


@router.get("/status", response_model=StatusOut)
async def status_now(exchange: ExchangeDep, top: int = 5) -> StatusOut:
    """اجرای یک چرخه‌ی تحلیل + تصمیم زنده."""
    bot = NooaahBot(exchange=exchange, config=NooaahConfig(top_n=top))
    result = await bot.run_once()
    proposal = None
    if result.proposal is not None:
        p = result.proposal
        proposal = ProposalOut(
            symbol=p.symbol,
            action=p.action,
            entry=round(p.entry, 2),
            take_profit=round(p.take_profit, 2),
            stop_loss=round(p.stop_loss, 2),
            confidence=p.confidence,
            regime=p.regime,
            reason=p.reason,
        )
    return StatusOut(
        symbols_analyzed=result.symbols_analyzed,
        duration_seconds=round(result.duration_seconds, 2),
        proposal=proposal,
        error=result.error,
    )


def _parse_date_utc(s: str) -> int:
    """ISO date (YYYY-MM-DD) → unix timestamp."""
    dt = datetime.strptime(s, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    return int(dt.timestamp())


def _find_idx_range(candles: list, start_ts: int, end_ts: int) -> tuple[int, int] | None:
    """پیدا کردن [start_idx, end_idx) با بازه. None اگه داده‌ی کافی نباشه."""
    start_idx = None
    end_idx = len(candles)
    for i, c in enumerate(candles):
        if start_idx is None and c.time >= start_ts:
            start_idx = i
        if c.time >= end_ts:
            end_idx = i
            break
    if start_idx is None or end_idx - start_idx < 50:
        return None
    return start_idx, end_idx


@router.get("/backtest", response_model=BacktestOut)
async def backtest(
    exchange: ExchangeDep,
    top: int = 5,
    limit: int = 700,
    symbols: str | None = None,
    start: str | None = None,
    end: str | None = None,
    conf: int = 85,
    cc: int = 2,
    tp: float = 3.0,
    sl: float = 1.5,
    vol_z_min: float = -0.5,
) -> BacktestOut:
    """اجرای backtest روی top نمادهای پرحجم.

    اگه start و end داده بشن → فقط اون بازه.
    پارامترهای Nooaah از query قابل override.
    """
    cfg = NooaahConfig(
        top_n=top,
        min_confidence=conf,
        confirmation_candles=cc,
        tp_atr_mult=tp,
        sl_atr_mult=sl,
        volume_z_min=vol_z_min,
    )
    bot = NooaahBot(exchange=exchange, config=cfg)
    if symbols:
        sym_list = [s.strip() for s in symbols.split(",") if s.strip()]
    else:
        sym_list = await bot.pick_top_symbols(top)
    if not sym_list:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="no markets returned from Wallex",
        )

    uc = GetCandlesUseCase(exchange=exchange)
    candles_by_symbol = {}
    for sym in sym_list:
        try:
            c = await uc.execute(symbol=sym, timeframe="1h", limit=limit)
            if c:
                candles_by_symbol[sym] = c
        except Exception:
            continue

    if not candles_by_symbol:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="no candles fetched",
        )

    # فیلتر تاریخ (اختیاری)
    start_idx = 0
    end_idx: int | None = None
    if start and end:
        start_ts = _parse_date_utc(start)
        end_ts = _parse_date_utc(end) + 86400
        if end_ts <= start_ts:
            raise HTTPException(400, "end must be after start")

        filtered = {}
        starts, ends = [], []
        for sym, candles in candles_by_symbol.items():
            rng = _find_idx_range(candles, start_ts, end_ts)
            if rng is None:
                continue
            s, e = rng
            filtered[sym] = candles
            starts.append(s)
            ends.append(e)

        if not filtered:
            raise HTTPException(400, "no symbols have data in requested range")

        candles_by_symbol = filtered
        start_idx = max(starts)
        end_idx = min(ends)
        if start_idx < 120:
            raise HTTPException(
                400,
                f"effective start_idx={start_idx} < warmup=120. "
                f"Move start date later or increase --limit."
            )

    try:
        stats = run_nooaah_backtest(
            candles_by_symbol, cfg,
            warmup=120,
            start_idx=start_idx, end_idx=end_idx,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e
    recent = [
        TradeOut(
            entry_price=str(t.entry_price),
            exit_price=str(t.exit_price),
            side=t.side,
            return_pct=round(t.return_pct, 3),
            exit_reason=t.exit_reason,
            confidence=t.confidence,
            duration_candles=t.duration_candles,
        )
        for t in stats.trades[-5:]
    ]
    return BacktestOut(
        symbols=list(candles_by_symbol.keys()),
        candles_analyzed=stats.candles_analyzed,
        signals_generated=stats.signals_generated,
        total_trades=stats.total_trades,
        wins=stats.wins,
        losses=stats.losses,
        win_rate=round(stats.win_rate, 2),
        total_return_pct=round(stats.total_return_pct, 2),
        max_drawdown_pct=round(stats.max_drawdown_pct, 2),
        profit_factor=round(stats.profit_factor, 2),
        sharpe_ratio=round(stats.sharpe_ratio, 3),
        avg_duration_candles=round(stats.avg_duration_candles, 1),
        equity_curve_full=stats.equity_curve_full,
        buy_hold_curve=stats.buy_hold_curve,
        recent_trades=recent,
    )
