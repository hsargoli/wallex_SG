"""Backtest Engine — تست قوانین سیگنال روی گذشته.

منطق:
  1. برای هر کندل i، از کندل‌های [0..i] استفاده می‌کنیم (بدون نگاه به آینده)
  2. اگه سیگنال BUY/SELL با اطمینان کافی صادر شد → پوزیشن باز
  3. SL/TP روی کندل‌های بعدی چک می‌شه
  4. اگه timeout شد → با قیمت close بسته می‌شه
"""

from dataclasses import dataclass, field
from decimal import Decimal

from app.domain.entities.candle import Candle
from app.services.signal_engine import SignalType, generate_signal


@dataclass(slots=True)
class Trade:
    entry_time: int
    exit_time: int
    entry_price: Decimal
    exit_price: Decimal
    side: str  # buy / sell
    stop_loss: Decimal
    take_profit: Decimal
    return_pct: float
    duration_candles: int
    exit_reason: str  # take_profit / stop_loss / timeout / signal_reverse
    confidence: int
    symbol: str = ""  # برای multi-symbol backtest


@dataclass(slots=True)
class BacktestResult:
    symbol: str
    timeframe: str
    candles_analyzed: int
    signals_generated: int = 0
    trades: list[Trade] = field(default_factory=list)
    # آمار
    total_trades: int = 0
    wins: int = 0
    losses: int = 0
    win_rate: float = 0.0
    avg_win_pct: float = 0.0
    avg_loss_pct: float = 0.0
    total_return_pct: float = 0.0
    profit_factor: float = 0.0
    max_drawdown_pct: float = 0.0
    sharpe_ratio: float = 0.0
    avg_duration_candles: float = 0.0
    equity_curve: list[float] = field(default_factory=list)
    # برای نمودار: نقطه‌به‌نقطه (per candle)، با benchmark
    equity_curve_full: list[float] = field(default_factory=list)
    buy_hold_curve: list[float] = field(default_factory=list)


def _gen_signal(candles_window: list[Candle]):
    return generate_signal(candles_window)


def run_backtest(
    candles: list[Candle],
    symbol: str,
    timeframe: str,
    min_confidence: int = 50,
    max_duration: int = 24,
    warmup: int = 100,
) -> BacktestResult:
    """
    اجرای backtest روی سری کندل‌ها.

    Args:
        candles: لیست کندل‌ها (صعودی)
        min_confidence: حداقل اطمینان برای ورود
        max_duration: حداکثر تعداد کندل در پوزیشن (timeout)
        warmup: تعداد کندل اولیه که نادیده گرفته می‌شه (برای محاسبه‌ی اندیکاتورها)
    """
    result = BacktestResult(symbol=symbol, timeframe=timeframe, candles_analyzed=len(candles))

    if len(candles) < warmup + 50:
        return result

    signals_generated = 0
    position: dict | None = None
    trades: list[Trade] = []

    equity = 100.0
    equity_curve = [equity]

    for i in range(warmup, len(candles)):
        window = candles[: i + 1]
        current = candles[i]

        # ---------- اگه پوزیشن باز نیست، دنبال ورود ----------
        if position is None:
            signal = _gen_signal(window)
            signals_generated += 1

            if (
                signal.type == SignalType.BUY
                and signal.confidence >= min_confidence
                and signal.stop_loss
                and signal.take_profit
            ):
                position = {
                    "side": "buy",
                    "entry_idx": i,
                    "entry_time": current.time,
                    "entry_price": current.close,
                    "stop_loss": signal.stop_loss,
                    "take_profit": signal.take_profit,
                    "confidence": signal.confidence,
                }
            elif (
                signal.type == SignalType.SELL
                and signal.confidence >= min_confidence
                and signal.stop_loss
                and signal.take_profit
            ):
                position = {
                    "side": "sell",
                    "entry_idx": i,
                    "entry_time": current.time,
                    "entry_price": current.close,
                    "stop_loss": signal.stop_loss,
                    "take_profit": signal.take_profit,
                    "confidence": signal.confidence,
                }
            continue

        # ---------- پوزیشن باز — بررسی خروج ----------
        exit_price: Decimal | None = None
        exit_reason = ""

        if position["side"] == "buy":
            if current.low <= position["stop_loss"]:
                exit_price = position["stop_loss"]
                exit_reason = "stop_loss"
            elif current.high >= position["take_profit"]:
                exit_price = position["take_profit"]
                exit_reason = "take_profit"
        else:  # sell
            if current.high >= position["stop_loss"]:
                exit_price = position["stop_loss"]
                exit_reason = "stop_loss"
            elif current.low <= position["take_profit"]:
                exit_price = position["take_profit"]
                exit_reason = "take_profit"

        # timeout
        if exit_price is None and (i - position["entry_idx"]) >= max_duration:
            exit_price = current.close
            exit_reason = "timeout"

        if exit_price is not None:
            entry_p = position["entry_price"]
            if position["side"] == "buy":
                ret = float((exit_price / entry_p - 1) * 100)
            else:
                ret = float((entry_p / exit_price - 1) * 100)

            trade = Trade(
                entry_time=position["entry_time"],
                exit_time=current.time,
                entry_price=entry_p,
                exit_price=exit_price,
                side=position["side"],
                stop_loss=position["stop_loss"],
                take_profit=position["take_profit"],
                return_pct=ret,
                duration_candles=i - position["entry_idx"],
                exit_reason=exit_reason,
                confidence=position["confidence"],
            )
            trades.append(trade)

            equity = equity * (1 + ret / 100)
            equity_curve.append(round(equity, 4))

            position = None

    # ---------- آمار ----------
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
        result.avg_duration_candles = sum(t.duration_candles for t in trades) / len(trades)

        gross_profit = sum(t.return_pct for t in wins)
        gross_loss = abs(sum(t.return_pct for t in losses))
        result.profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0.0

        # max drawdown
        peak = equity_curve[0]
        max_dd = 0.0
        for e in equity_curve:
            if e > peak:
                peak = e
            dd = (peak - e) / peak * 100
            if dd > max_dd:
                max_dd = dd
        result.max_drawdown_pct = max_dd

        # Sharpe (ساده)
        returns = [t.return_pct for t in trades]
        if len(returns) > 1:
            avg_ret = sum(returns) / len(returns)
            variance = sum((r - avg_ret) ** 2 for r in returns) / (len(returns) - 1)
            std = variance**0.5
            if std > 0:
                result.sharpe_ratio = avg_ret / std

    result.equity_curve = equity_curve
    return result
