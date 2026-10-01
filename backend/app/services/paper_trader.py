"""Paper Trader — ربات مجازی برای تست استراتژی.

ویژگی‌ها:
  - حلقه‌ی تصمیم‌گیری خودکار (هر N ثانیه)
  - ورود: ML + قوانین (OR)
  - خروج: TP/SL/Timeout
  - لاگ همه تریدها
  - ذخیره‌ی state روی دیسک
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from app.application.use_cases.get_candles import GetCandlesUseCase
from app.domain.entities.candle import Candle
from app.domain.ports.exchange import ExchangePort
from app.services.bottom_detector import detect_bottom
from app.services.ml_bottom_model import (
    build_features,
    candles_to_df,
    load_model,
)
from app.services.scalping_strategy import (
    STOP_LOSS_PCT,
    TAKE_PROFIT_PCT,
)

STATE_DIR = Path("data/paper_trading")
STATE_FILE = STATE_DIR / "state.json"
TRADES_FILE = STATE_DIR / "trades.jsonl"


# ---------- Dataclasses ----------
@dataclass
class PaperPosition:
    symbol: str
    entry_price: float
    quantity: float
    tp: float
    sl: float
    entry_time: int
    entry_idx: int
    ml_prob: float | None
    rule_score: int
    reason: str


@dataclass
class PaperTrade:
    symbol: str
    entry_time: int
    exit_time: int
    entry_price: float
    exit_price: float
    quantity: float
    pnl_pct: float
    pnl_tmn: float
    exit_reason: str
    duration_candles: int
    ml_prob: float | None
    rule_score: int


@dataclass
class PaperState:
    """State ربات — قابل ذخیره و بازیابی."""

    is_running: bool = False
    initial_capital: float = 300_000.0
    capital: float = 300_000.0
    peak_capital: float = 300_000.0
    max_drawdown_pct: float = 0.0
    total_trades: int = 0
    wins: int = 0
    losses: int = 0
    last_check_time: int = 0
    open_positions: list[dict[str, Any]] = field(default_factory=list)
    recent_trades: list[dict[str, Any]] = field(default_factory=list)
    equity_curve: list[dict[str, Any]] = field(default_factory=list)


# ---------- Config ----------
@dataclass
class PaperConfig:
    symbols: list[str] = field(
        default_factory=lambda: [
            "BTCTMN",
            "ETHTMN",
            "XRPTMN",
            "DOGETMN",
            "SOLTMN",
        ]
    )
    timeframe: str = "15m"
    check_interval_sec: int = 60  # هر ۶۰ ثانیه
    max_positions: int = 2
    capital_per_position_pct: float = 0.5
    ml_threshold: float = 0.55
    rule_min_score: int = 5
    warmup_candles: int = 100
    max_duration_candles: int = 24
    fee_pct: float = 0.2
    use_ml: bool = True
    use_rules: bool = True


# ---------- Service ----------
class PaperTrader:
    def __init__(self, config: PaperConfig | None = None):
        self.config = config or PaperConfig()
        self.state = PaperState()
        self._task: asyncio.Task | None = None
        self._model = None
        self._exchange: ExchangePort | None = None
        self._lock = asyncio.Lock()

    # ---------- Persistence ----------
    def _ensure_dir(self):
        STATE_DIR.mkdir(parents=True, exist_ok=True)

    def save_state(self):
        self._ensure_dir()
        data = asdict(self.state)
        STATE_FILE.write_text(json.dumps(data, indent=2, default=str))

    def load_state(self):
        if STATE_FILE.exists():
            try:
                data = json.loads(STATE_FILE.read_text())
                for key, val in data.items():
                    if hasattr(self.state, key):
                        setattr(self.state, key, val)
            except Exception:
                pass

    def append_trade(self, trade: PaperTrade):
        self._ensure_dir()
        with TRADES_FILE.open("a") as f:
            f.write(json.dumps(asdict(trade), default=str) + "\n")

    # ---------- Model ----------
    def _load_model(self):
        if self._model is None:
            try:
                self._model = load_model()
            except FileNotFoundError:
                self._model = None
        return self._model

    # ---------- Core Logic ----------
    async def _fetch_candles(self, symbol: str) -> list[Candle]:
        if self._exchange is None:
            return []
        try:
            uc = GetCandlesUseCase(exchange=self._exchange)
            return await uc.execute(
                symbol=symbol,
                timeframe=self.config.timeframe,
                limit=300,
            )
        except Exception:
            return []

    def _predict_ml(self, candles: list[Candle]) -> float | None:
        if not self.config.use_ml or self._model is None:
            return None
        if len(candles) < self.config.warmup_candles:
            return None
        try:
            df = candles_to_df(candles)
            X = build_features(df)
            last = X.iloc[[-1]]
            if last.isna().any(axis=1).iloc[0]:
                return None
            prob = self._model.predict_proba(last)[0]
            return float(prob[1])
        except Exception:
            return None

    async def _check_exits(self) -> None:
        """چک خروج از پوزیشن‌های باز."""
        async with self._lock:
            positions_to_remove = []
            for i, pos_data in enumerate(self.state.open_positions):
                symbol = pos_data["symbol"]
                candles = await self._fetch_candles(symbol)
                if not candles:
                    continue

                current = candles[-1]
                current_idx = len(candles) - 1
                pos = PaperPosition(**pos_data)

                exit_price = None
                reason = ""

                if current.high >= pos.tp:
                    exit_price = pos.tp
                    reason = "take_profit"
                elif current.low <= pos.sl:
                    exit_price = pos.sl
                    reason = "stop_loss"
                elif (current_idx - pos.entry_idx) >= self.config.max_duration_candles:
                    exit_price = float(current.close)
                    reason = "timeout"

                if exit_price is not None:
                    pnl_pct = (exit_price / pos.entry_price - 1) * 100 - self.config.fee_pct
                    pnl_tmn = pos.quantity * exit_price - pos.quantity * pos.entry_price
                    pnl_tmn -= (pos.quantity * pos.entry_price + pos.quantity * exit_price) * (
                        self.config.fee_pct / 200
                    )

                    self.state.capital += pnl_tmn
                    if self.state.capital > self.state.peak_capital:
                        self.state.peak_capital = self.state.capital

                    dd = (
                        (self.state.peak_capital - self.state.capital)
                        / self.state.peak_capital
                        * 100
                    )
                    if dd > self.state.max_drawdown_pct:
                        self.state.max_drawdown_pct = dd

                    if pnl_pct > 0:
                        self.state.wins += 1
                    else:
                        self.state.losses += 1
                    self.state.total_trades += 1

                    trade = PaperTrade(
                        symbol=symbol,
                        entry_time=pos.entry_time,
                        exit_time=current.time,
                        entry_price=pos.entry_price,
                        exit_price=exit_price,
                        quantity=pos.quantity,
                        pnl_pct=pnl_pct,
                        pnl_tmn=pnl_tmn,
                        exit_reason=reason,
                        duration_candles=current_idx - pos.entry_idx,
                        ml_prob=pos.ml_prob,
                        rule_score=pos.rule_score,
                    )
                    self.append_trade(trade)
                    self.state.recent_trades.insert(0, asdict(trade))
                    self.state.recent_trades = self.state.recent_trades[:50]
                    self.state.equity_curve.append(
                        {
                            "time": current.time,
                            "capital": round(self.state.capital, 1),
                        }
                    )
                    positions_to_remove.append(i)

            for i in reversed(positions_to_remove):
                self.state.open_positions.pop(i)

    async def _check_entries(self) -> None:
        """چک ورود به پوزیشن‌های جدید."""
        if len(self.state.open_positions) >= self.config.max_positions:
            return

        # نمادهایی که در پوزیشن هستن رو skip کن
        open_symbols = {p["symbol"] for p in self.state.open_positions}

        for symbol in self.config.symbols:
            if symbol in open_symbols:
                continue
            if len(self.state.open_positions) >= self.config.max_positions:
                break

            candles = await self._fetch_candles(symbol)
            if len(candles) < self.config.warmup_candles:
                continue

            # ML
            ml_prob = self._predict_ml(candles)

            # Rules
            rule = detect_bottom(candles)

            # Decision (OR)
            ml_ok = ml_prob is not None and ml_prob >= self.config.ml_threshold
            rule_ok = rule.is_bottom and rule.score >= self.config.rule_min_score

            if not (ml_ok or rule_ok):
                continue

            # باز کردن پوزیشن
            entry_price = float(candles[-1].close)
            capital_per_pos = self.state.initial_capital * self.config.capital_per_position_pct
            invest = min(capital_per_pos, self.state.capital * 0.9)
            if invest < 10_000:
                continue

            quantity = invest / entry_price
            tp = entry_price * (1 + float(TAKE_PROFIT_PCT) / 100)
            sl = entry_price * (1 - float(STOP_LOSS_PCT) / 100)

            reasons = []
            if ml_ok:
                reasons.append(f"ML={ml_prob:.2f}")
            if rule_ok:
                reasons.append(f"score={rule.score}")

            pos = PaperPosition(
                symbol=symbol,
                entry_price=entry_price,
                quantity=quantity,
                tp=tp,
                sl=sl,
                entry_time=candles[-1].time,
                entry_idx=len(candles) - 1,
                ml_prob=ml_prob,
                rule_score=rule.score,
                reason=" | ".join(reasons),
            )
            self.state.open_positions.append(asdict(pos))

    async def _loop(self):
        """حلقه‌ی اصلی."""
        while self.state.is_running:
            try:
                self.state.last_check_time = int(time.time())
                await self._check_exits()
                await self._check_entries()
                self.save_state()
            except Exception as e:
                print(f"⚠️ Paper trading loop error: {e}")

            await asyncio.sleep(self.config.check_interval_sec)

    # ---------- Public API ----------
    async def start(self, exchange: ExchangePort):
        if self.state.is_running:
            return {"status": "already_running"}

        self._exchange = exchange
        self._load_model()

        # بازیابی state اگر قبلاً داشته
        if not self.state.open_positions and self.state.total_trades == 0:
            self.load_state()

        self.state.is_running = True
        self._task = asyncio.create_task(self._loop())
        return {"status": "started"}

    async def stop(self):
        self.state.is_running = False
        if self._task:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
        self.save_state()
        return {"status": "stopped"}

    def reset(self):
        self.state = PaperState()
        self.save_state()
        return {"status": "reset"}

    def get_status(self) -> dict:
        s = self.state
        win_rate = (s.wins / s.total_trades * 100) if s.total_trades > 0 else 0
        total_return_pct = (s.capital - s.initial_capital) / s.initial_capital * 100
        return {
            "is_running": s.is_running,
            "initial_capital": s.initial_capital,
            "current_capital": round(s.capital, 1),
            "total_return_pct": round(total_return_pct, 2),
            "max_drawdown_pct": round(s.max_drawdown_pct, 2),
            "total_trades": s.total_trades,
            "wins": s.wins,
            "losses": s.losses,
            "win_rate": round(win_rate, 2),
            "open_positions": s.open_positions,
            "recent_trades": s.recent_trades[:20],
            "equity_curve": s.equity_curve[-100:],
            "last_check_time": s.last_check_time,
            "config": asdict(self.config),
        }


# Singleton
paper_trader = PaperTrader()
