"""PaperState — state کامل Paper Trading."""

from dataclasses import dataclass, field, asdict
from typing import Any


@dataclass
class PaperState:
    """State کامل."""

    is_running: bool = False
    initial_capital: float = 1000.0
    capital: float = 1000.0
    equity: float = 1000.0
    peak_capital: float = 1000.0
    peak_equity: float = 1000.0
    max_drawdown_pct: float = 0.0
    total_trades: int = 0
    wins: int = 0
    losses: int = 0
    total_pnl: float = 0.0
    total_pnl_pct: float = 0.0
    win_rate: float = 0.0
    open_positions: list[dict[str, Any]] = field(default_factory=list)
    recent_trades: list[dict[str, Any]] = field(default_factory=list)
    events: list[dict[str, Any]] = field(default_factory=list)
    equity_curve: list[dict[str, Any]] = field(default_factory=list)
    radar: list[dict[str, Any]] = field(default_factory=list)
    started_at: int = 0
    last_check_at: int = 0
    check_count: int = 0

    def to_dict(self) -> dict:
        return asdict(self)

    def update_metrics(self) -> None:
        """محاسبه معیارها بر اساس equity."""
        # ۱. equity = نقد + ارزش پوزیشن‌های باز
        position_value = sum(
            p.get("quantity", 0) * p.get("current_price", p.get("entry_price", 0))
            for p in self.open_positions
        )
        self.equity = self.capital + position_value

        # ۲. PnL بر اساس equity
        self.total_pnl = self.equity - self.initial_capital
        if self.initial_capital > 0:
            self.total_pnl_pct = (self.total_pnl / self.initial_capital) * 100

        # ۳. Peak بر اساس equity
        if self.equity > self.peak_equity:
            self.peak_equity = self.equity

        # ۴. Max DD بر اساس equity
        if self.peak_equity > 0:
            dd = (self.peak_equity - self.equity) / self.peak_equity * 100
            if dd > self.max_drawdown_pct:
                self.max_drawdown_pct = dd

        # ۵. Win Rate
        if self.total_trades > 0:
            self.win_rate = (self.wins / self.total_trades) * 100
