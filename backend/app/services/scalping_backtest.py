"""Scalping Backtest — تست استراتژی روی چند مارکت."""

from dataclasses import dataclass, field
from decimal import Decimal

from app.domain.entities.candle import Candle
from app.services.scalping_strategy import Position, check_exit, evaluate_entry


@dataclass
class ScalpingTrade:
    symbol: str
    entry_time: int
    exit_time: int
    entry_price: Decimal
    exit_price: Decimal
    pnl_tmn: float
    pnl_pct: float
    exit_reason: str
    duration_candles: int


@dataclass
class ScalpingBacktestResult:
    initial_capital: float
    final_capital: float
    total_trades: int
    wins: int
    losses: int
    win_rate: float
    total_return_pct: float
    max_drawdown_pct: float
    avg_win_pct: float
    avg_loss_pct: float
    trades: list[ScalpingTrade] = field(default_factory=list)
    equity_curve: list[float] = field(default_factory=list)


def run_scalping_backtest(
    markets_data: dict[str, list[Candle]],
    initial_capital: float = 300_000,
    max_positions: int = 2,
    capital_per_position_pct: float = 0.5,
) -> ScalpingBacktestResult:
    capital = initial_capital
    capital_per_pos = initial_capital * capital_per_position_pct

    open_positions: dict[str, Position] = {}
    trades: list[ScalpingTrade] = []
    equity_curve = [capital]

    all_candles: list[tuple[str, int, Candle]] = []
    for symbol, candles in markets_data.items():
        for i, c in enumerate(candles):
            all_candles.append((symbol, i, c))
    all_candles.sort(key=lambda x: x[2].time)

    warmup = 100

    for symbol, idx, candle in all_candles:
        if idx < warmup:
            continue

        to_close: list[str] = []
        for pos_symbol, pos in open_positions.items():
            if pos_symbol != symbol:
                continue
            should_exit, reason = check_exit(pos, candle, idx)
            if should_exit:
                if reason == "take_profit":
                    exit_price = pos.take_profit
                elif reason == "stop_loss":
                    exit_price = pos.stop_loss
                else:
                    exit_price = candle.close

                pnl_pct = float((exit_price - pos.entry_price) / pos.entry_price * 100)
                pnl_pct_net = pnl_pct - 0.2
                value = float(pos.quantity * exit_price)
                pnl_tmn = value * (pnl_pct_net / 100)
                capital += pnl_tmn

                trades.append(ScalpingTrade(
                    symbol=pos_symbol,
                    entry_time=pos.entry_time,
                    exit_time=candle.time,
                    entry_price=pos.entry_price,
                    exit_price=exit_price,
                    pnl_tmn=pnl_tmn,
                    pnl_pct=pnl_pct_net,
                    exit_reason=reason,
                    duration_candles=idx - pos.entry_candle_idx,
                ))
                equity_curve.append(capital)
                to_close.append(pos_symbol)

        for s in to_close:
            del open_positions[s]

        if len(open_positions) >= max_positions:
            continue
        if symbol in open_positions:
            continue
        if capital < capital_per_pos * 0.8:
            continue

        candles_up_to = markets_data[symbol][: idx + 1]
        if len(candles_up_to) < warmup:
            continue

        entry = evaluate_entry(candles_up_to, symbol)
        if entry is None:
            continue

        invest = min(capital_per_pos, capital)
        qty = Decimal(str(invest)) / entry.price

        open_positions[symbol] = Position(
            symbol=symbol,
            entry_price=entry.price,
            quantity=qty,
            take_profit=entry.take_profit,
            stop_loss=entry.stop_loss,
            entry_time=candle.time,
            entry_candle_idx=idx,
        )

    wins = [t for t in trades if t.pnl_pct > 0]
    losses = [t for t in trades if t.pnl_pct <= 0]

    peak = equity_curve[0]
    max_dd = 0.0
    for e in equity_curve:
        if e > peak:
            peak = e
        dd = (peak - e) / peak * 100
        if dd > max_dd:
            max_dd = dd

    return ScalpingBacktestResult(
        initial_capital=initial_capital,
        final_capital=capital,
        total_trades=len(trades),
        wins=len(wins),
        losses=len(losses),
        win_rate=(len(wins) / len(trades) * 100) if trades else 0.0,
        total_return_pct=(capital - initial_capital) / initial_capital * 100,
        max_drawdown_pct=max_dd,
        avg_win_pct=(sum(t.pnl_pct for t in wins) / len(wins)) if wins else 0.0,
        avg_loss_pct=(sum(t.pnl_pct for t in losses) / len(losses)) if losses else 0.0,
        trades=trades,
        equity_curve=equity_curve,
    )
