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
from app.services.bots.nooaah.strategy import decide

WARMUP = 200
FEE_PCT = 0.2


def run_nooaah_backtest(
    candles_by_symbol: dict[str, Sequence[Candle]],
    config: NooaahConfig,
    max_duration: int = 24,
    warmup: int = WARMUP,
    start_idx: int = 0,
    end_idx: int | None = None,
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
    position: dict | None = None
    trades: list[Trade] = []

    equity = 100.0
    equity_curve = [equity]
    equity_curve_full: list[float] = []

    # benchmark: buy-and-hold برابر وزن از همه‌ی نمادها
    start_closes: dict[str, float] = {
        sym: float(c[effective_start].close)
        for sym, c in candles_by_symbol.items()
    }
    buy_hold_curve: list[float] = []

    for i in range(effective_start, effective_end):
        current_time = candles_by_symbol[first_symbol][i].time

        # benchmark per candle
        avg = sum(
            (float(c[i].close) / start_closes[sym]) * 100
            for sym, c in candles_by_symbol.items()
            if start_closes[sym] > 0
        ) / len(start_closes)
        buy_hold_curve.append(round(avg, 4))

        # ---- اگر پوزیشن باز هست، چک خروج ----
        if position is not None:
            sym = position["symbol"]
            current = candles_by_symbol[sym][i]
            exit_price: Decimal | None = None
            exit_reason = ""

            if current.low <= position["stop_loss"]:
                exit_price = position["stop_loss"]
                exit_reason = "stop_loss"
            elif current.high >= position["take_profit"]:
                exit_price = position["take_profit"]
                exit_reason = "take_profit"

            if exit_price is None and (i - position["entry_idx"]) >= max_duration:
                exit_price = current.close
                exit_reason = "timeout"

            if exit_price is not None:
                entry_p = position["entry_price"]
                ret = float((exit_price / entry_p - 1) * 100) - FEE_PCT
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
                    )
                )
                equity *= (1 + ret / 100)
                equity_curve.append(round(equity, 4))
                position = None
            equity_curve_full.append(round(equity, 4))
            continue

        # ---- تصمیم جدید ----
        windows = {
            sym: c[i - warmup : i] for sym, c in candles_by_symbol.items()
        }
        signals_generated += 1
        proposal = decide(windows, config)

        if proposal is None:
            equity_curve_full.append(round(equity, 4))
            continue

        current = candles_by_symbol[proposal.symbol][i]
        position = {
            "symbol": proposal.symbol,
            "entry_idx": i,
            "entry_time": current.time,
            "entry_price": Decimal(str(proposal.entry)),
            "stop_loss": Decimal(str(proposal.stop_loss)),
            "take_profit": Decimal(str(proposal.take_profit)),
            "confidence": proposal.confidence,
        }
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

        returns = [t.return_pct for t in trades]
        if len(returns) > 1:
            avg_ret = sum(returns) / len(returns)
            variance = sum((r - avg_ret) ** 2 for r in returns) / (
                len(returns) - 1
            )
            std = variance ** 0.5
            if std > 0:
                result.sharpe_ratio = avg_ret / std

    result.equity_curve = equity_curve
    result.equity_curve_full = equity_curve_full
    result.buy_hold_curve = buy_hold_curve
    return result
