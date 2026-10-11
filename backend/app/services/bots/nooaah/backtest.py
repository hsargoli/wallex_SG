"""Nooaah backtest — reuse موجود، تصمیم جدید.

از Trade و BacktestResult در services/backtest.py استفاده می‌کنه.
فقط «تصمیم» جدیدـه: decide() روی چند نماد (multi-symbol).
"""

from __future__ import annotations

from decimal import Decimal
from typing import Sequence

from app.domain.entities.candle import Candle
from app.services.backtest import BacktestResult, Trade
from app.services.bots.nooaah.config import NooaahConfig
from app.services.bots.nooaah.strategy import decide, should_exit_on_momentum

WARMUP = 200
FEE_PCT = 0.2


def run_nooaah_backtest(
    candles_by_symbol: dict[str, Sequence[Candle]],
    config: NooaahConfig,
    max_duration: int = 24,
    warmup: int = WARMUP,
    start_idx: int = 0,
    end_idx: int | None = None,
    candles_1m_by_symbol: dict[str, Sequence[Candle]] | None = None,
) -> BacktestResult:
    """backtest چندنمادی Nooaah.

    فرض: ۵ نماد فعلی در گذشته هم پرحجم بودن (approximation).
    """
    result = BacktestResult(
        symbol="NOOAAH_MULTI",
        timeframe="1h",
        candles_analyzed=sum(len(c) for c in candles_by_symbol.values()),
    )

    if not candles_by_symbol:
        return result

    min_len = min(len(c) for c in candles_by_symbol.values())

    # effective trading window
    effective_start = max(start_idx, warmup)
    effective_end = end_idx if end_idx is not None else min_len

    if effective_end - effective_start < 50:
        raise ValueError(
            f"trading window too small: [{effective_start}, {effective_end}) "
            f"= {effective_end - effective_start} candles, need ≥ 50. "
            f"(data={min_len}, warmup={warmup}, start_idx={start_idx}, "
            f"end_idx={end_idx})"
        )

    first_symbol = next(iter(candles_by_symbol))

    signals_generated = 0
    positions: list[dict] = []
    trades: list[Trade] = []
    last_sl_idx: dict[str, int] = {}  # B3: آخرین ایندکس SL برای هر نماد

    # C1: daily loss tracking
    DAY_SECONDS = 86400
    current_day = None
    daily_pnl_pct = 0.0

    equity = 100.0
    equity_curve = [equity]
    equity_curve_full: list[float] = []

    # benchmark: buy-and-hold برابر وزن از همه‌ی نمادها
    start_closes: dict[str, float] = {
        sym: float(c[effective_start].close)
        for sym, c in candles_by_symbol.items()
    }

    # index 1m candles by (symbol, hour_start) — per-symbol
    hour_1m: dict[tuple[str, int], list[Candle]] = {}
    if candles_1m_by_symbol and config.momentum_exit_candles > 0:
        for sym, lst in candles_1m_by_symbol.items():
            for c in lst:
                h = (c.time // 3600) * 3600
                hour_1m.setdefault((sym, h), []).append(c)
    buy_hold_curve: list[float] = []

    for i in range(effective_start, effective_end):
        current_time = candles_by_symbol[first_symbol][i].time

        # C1: reset روزانه
        this_day = current_time // DAY_SECONDS
        if current_day is None or this_day != current_day:
            current_day = this_day
            daily_pnl_pct = 0.0

        # benchmark per candle
        avg = sum(
            (float(c[i].close) / start_closes[sym]) * 100
            for sym, c in candles_by_symbol.items()
            if start_closes[sym] > 0
        ) / len(start_closes)
        buy_hold_curve.append(round(avg, 4))

        # ---- چک خروج همه‌ی پوزیشن‌های باز ----
        closed_any = False
        for position in list(positions):
            sym = position["symbol"]
            current = candles_by_symbol[sym][i]
            exit_price: Decimal | None = None
            exit_reason = ""

            # peak tracking (برای trailing)
            current_high_f = float(current.high)
            if current_high_f > position["peak_high"]:
                position["peak_high"] = current_high_f

            if config.use_trailing:
                # effective SL = max(initial_SL, peak - trailing_atr_mult × ATR)
                initial_sl_f = float(position["stop_loss"])
                trailing_sl_f = (
                    position["peak_high"]
                    - position["atr_abs"] * config.trailing_atr_mult
                )
                effective_sl_f = max(initial_sl_f, trailing_sl_f)
                effective_sl = Decimal(str(effective_sl_f))

                if current.low <= effective_sl:
                    exit_price = effective_sl
                    # اگه SL بالاتر از initial رفت → trailing
                    exit_reason = (
                        "trailing"
                        if effective_sl_f > initial_sl_f + 1e-9
                        else "stop_loss"
                    )
            else:
                if current.low <= position["stop_loss"]:
                    exit_price = position["stop_loss"]
                    exit_reason = "stop_loss"
                elif current.high >= position["take_profit"]:
                    exit_price = position["take_profit"]
                    exit_reason = "take_profit"

            if exit_price is None and (i - position["entry_idx"]) >= max_duration:
                exit_price = current.close
                exit_reason = "timeout"

            # momentum exit (اگر هنوز بازه و فعاله)
            if (
                exit_price is None
                and config.momentum_exit_candles > 0
                and hour_1m
                and i > position["entry_idx"]  # فقط بعد از ساعت ورود
            ):
                h_start = (current.time // 3600) * 3600
                m1 = hour_1m.get((position["symbol"], h_start))
                if m1 and should_exit_on_momentum(
                    m1,
                    window=config.momentum_exit_candles,
                    red_ratio=config.momentum_red_ratio,
                    mode=config.momentum_mode,
                    consecutive=config.momentum_consecutive,
                    cumulative_pct=config.momentum_cumulative_pct,
                ):
                    exit_price = current.close
                    exit_reason = "momentum"

            if exit_price is not None:
                entry_p = position["entry_price"]
                ret = float((exit_price / entry_p - 1) * 100) - FEE_PCT
                size_mult = position.get("size_mult", 1.0)
                weighted_ret = ret * size_mult
                trades.append(
                    Trade(
                        entry_time=position["entry_time"],
                        exit_time=current.time,
                        entry_price=entry_p,
                        exit_price=exit_price,
                        side="buy",
                        stop_loss=position["stop_loss"],
                        take_profit=position["take_profit"],
                        return_pct=ret,
                        duration_candles=i - position["entry_idx"],
                        exit_reason=exit_reason,
                        confidence=position["confidence"],
                        symbol=position["symbol"],
                    )
                )
                # B3: اگه SL خورد → ثبت
                if exit_reason == "stop_loss":
                    last_sl_idx[position["symbol"]] = i

                # C1: به‌روزرسانی daily pnl
                daily_pnl_pct += weighted_ret

                # با max_concurrent > 1، پوزیشن به سهم مساوی باز می‌شود
                capital_fraction = 1.0 / max(config.max_concurrent_positions, 1)
                equity *= (1 + weighted_ret * capital_fraction / 100)
                equity_curve.append(round(equity, 4))
                positions.remove(position)
                closed_any = True

        equity_curve_full.append(round(equity, 4))

        # اگه هر پوزیشنی این کندل بسته شد → entry نکن (backward-compat با تک‌پوزیشن)
        if closed_any:
            continue

        # ---- تصمیم جدید (فقط اگه جا هست) ----
        signals_generated += 1

        # B2: چک space
        if len(positions) >= config.max_concurrent_positions:
            equity_curve_full.append(round(equity, 4))
            continue

        windows = {
            sym: c[i - warmup : i] for sym, c in candles_by_symbol.items()
        }
        proposal = decide(windows, config)

        # B2: skip symbols already held
        held = {p["symbol"] for p in positions}
        if proposal is not None and proposal.symbol in held:
            proposal = None

        # B3: cooldown filter
        if proposal is not None and config.cooldown_after_sl > 0:
            last = last_sl_idx.get(proposal.symbol)
            if last is not None and (i - last) < config.cooldown_after_sl:
                proposal = None

        # C1: daily loss limit
        if proposal is not None and config.daily_loss_limit < 100.0:
            if daily_pnl_pct <= -config.daily_loss_limit:
                proposal = None

        if proposal is None:
            equity_curve_full.append(round(equity, 4))
            continue

        current = candles_by_symbol[proposal.symbol][i]
        # atr_abs از فاصله‌ی entry→SL استخراج می‌شه
        atr_abs = (proposal.entry - proposal.stop_loss) / max(config.sl_atr_mult, 0.01)
        positions.append({
            "symbol": proposal.symbol,
            "entry_idx": i,
            "entry_time": current.time,
            "entry_price": Decimal(str(proposal.entry)),
            "stop_loss": Decimal(str(proposal.stop_loss)),
            "take_profit": Decimal(str(proposal.take_profit)),
            "confidence": proposal.confidence,
            "atr_abs": atr_abs,
            "peak_high": proposal.entry,
            "size_mult": proposal.size_mult,
        })
        equity_curve_full.append(round(equity, 4))

    # ---- آمار ----
    result.signals_generated = signals_generated
    result.trades = trades
    result.total_trades = len(trades)

    if trades:
        wins = [t for t in trades if t.return_pct > 0]
        losses = [t for t in trades if t.return_pct <= 0]

        result.wins = len(wins)
        result.losses = len(losses)
        result.win_rate = (len(wins) / len(trades)) * 100

        if wins:
            result.avg_win_pct = sum(t.return_pct for t in wins) / len(wins)
        if losses:
            result.avg_loss_pct = sum(t.return_pct for t in losses) / len(losses)

        result.total_return_pct = equity - 100
        result.avg_duration_candles = (
            sum(t.duration_candles for t in trades) / len(trades)
        )

        gross_profit = sum(t.return_pct for t in wins)
        gross_loss = abs(sum(t.return_pct for t in losses))
        result.profit_factor = (
            gross_profit / gross_loss if gross_loss > 0 else 0.0
        )

        peak = equity_curve[0]
        max_dd = 0.0
        for e in equity_curve:
            if e > peak:
                peak = e
            dd = (peak - e) / peak * 100
            if dd > max_dd:
                max_dd = dd
        result.max_drawdown_pct = max_dd

        # Sharpe از equity curve (weighted)
        if len(equity_curve) > 2:
            eq_returns = [
                (equity_curve[i] - equity_curve[i-1]) / equity_curve[i-1]
                for i in range(1, len(equity_curve))
            ]
            if len(eq_returns) > 1:
                avg_r = sum(eq_returns) / len(eq_returns)
                var = sum((r - avg_r) ** 2 for r in eq_returns) / (len(eq_returns) - 1)
                std = var ** 0.5
                if std > 0:
                    result.sharpe_ratio = avg_r / std

    result.equity_curve = equity_curve
    result.equity_curve_full = equity_curve_full
    result.buy_hold_curve = buy_hold_curve
    return result
