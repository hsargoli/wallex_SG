"""Paper Trader v2 — با Smart Dispatcher."""

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
from app.services.bounce_scalper import check_bounce_exit
from app.services.simple_bot import check_simple_exit
from app.services.smart_dispatcher import dispatcher

STATE_DIR = Path("data/paper_v2")
STATE_FILE = STATE_DIR / "state.json"
TRADES_FILE = STATE_DIR / "trades.jsonl"


@dataclass
class PaperPosition:
    symbol: str
    strategy: str
    entry_price: float
    quantity: float
    tp: float
    sl: float
    entry_time: int
    entry_idx: int
    reason: str


@dataclass
class PaperTrade:
    symbol: str
    strategy: str
    entry_time: int
    exit_time: int
    entry_price: float
    exit_price: float
    pnl_pct: float
    pnl_tmn: float
    exit_reason: str
    duration_minutes: int


@dataclass
class PaperState:
    is_running: bool = False
    initial_capital: float = 300_000.0
    capital: float = 300_000.0
    peak_capital: float = 300_000.0
    max_drawdown_pct: float = 0.0
    total_trades: int = 0
    wins: int = 0
    losses: int = 0
    last_check_time: int = 0
    started_at: int = 0
    open_positions: list[dict[str, Any]] = field(default_factory=list)
    recent_trades: list[dict[str, Any]] = field(default_factory=list)
    equity_curve: list[dict[str, Any]] = field(default_factory=list)
    active_symbols: list[str] = field(default_factory=list)


@dataclass
class PaperConfig:
    check_interval_sec: int = 180  # هر ۳ دقیقه (کندل 15m = هر 15 دقیقه کامل)
    timeframe: str = "15m"
    max_positions: int = 3
    position_size_pct: float = 30.0  # 30% هر پوزیشن
    fee_pct: float = 0.2
    max_duration_candles: int = 20  # همون timeout های استراتژی
    warmup_candles: int = 50


class PaperTraderV2:
    def __init__(self, config: PaperConfig | None = None):
        self.config = config or PaperConfig()
        self.state = PaperState()
        self._task: asyncio.Task | None = None
        self._exchange: ExchangePort | None = None
        self._lock = asyncio.Lock()

    # ---------- Persistence ----------
    def _ensure_dir(self):
        STATE_DIR.mkdir(parents=True, exist_ok=True)

    def save_state(self):
        self._ensure_dir()
        STATE_FILE.write_text(json.dumps(asdict(self.state), indent=2, default=str))

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

    # ---------- Data ----------
    async def _fetch_candles(self, symbol: str) -> list[Candle]:
        if self._exchange is None:
            return []
        try:
            uc = GetCandlesUseCase(exchange=self._exchange)
            return await uc.execute(
                symbol=symbol,
                timeframe=self.config.timeframe,
                limit=500,
            )
        except Exception:
            return []

    # ---------- Exits ----------
    async def _check_exits(self):
        async with self._lock:
            to_remove = []
            for i, pos_data in enumerate(self.state.open_positions):
                symbol = pos_data["symbol"]
                strategy = pos_data["strategy"]
                candles = await self._fetch_candles(symbol)
                if not candles:
                    continue

                current = candles[-1]
                current_idx = len(candles) - 1
                # محاسبه ی candles در پوزیشن (تقریبی)
                candles_in_pos = current_idx - pos_data.get("entry_idx", current_idx)
                if candles_in_pos < 0:
                    candles_in_pos = 0

                # از تابع exit مناسب استفاده کن
                if strategy == "simple":
                    should_exit, exit_price, reason = check_simple_exit(
                        pos_data["entry_price"],
                        pos_data["tp"],
                        pos_data["sl"],
                        current,
                        candles_in_pos,
                    )
                else:  # bounce
                    should_exit, exit_price, reason = check_bounce_exit(
                        pos_data["entry_price"],
                        pos_data["tp"],
                        pos_data["sl"],
                        current,
                        candles_in_pos,
                    )

                if should_exit:
                    pnl_pct = (exit_price / pos_data["entry_price"] - 1) * 100 - self.config.fee_pct
                    pnl_tmn = pos_data["quantity"] * (exit_price - pos_data["entry_price"])
                    pnl_tmn -= (
                        pos_data["quantity"]
                        * (pos_data["entry_price"] + exit_price)
                        * (self.config.fee_pct / 200)
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
                        strategy=strategy,
                        entry_time=pos_data["entry_time"],
                        exit_time=current.time,
                        entry_price=pos_data["entry_price"],
                        exit_price=exit_price,
                        pnl_pct=round(pnl_pct, 3),
                        pnl_tmn=round(pnl_tmn, 1),
                        exit_reason=reason,
                        duration_minutes=int((current.time - pos_data["entry_time"]) / 60),
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
                    to_remove.append(i)

            for i in reversed(to_remove):
                self.state.open_positions.pop(i)

    # ---------- Entries ----------
    async def _check_entries(self):
        if len(self.state.open_positions) >= self.config.max_positions:
            return

        open_symbols = {p["symbol"] for p in self.state.open_positions}
        active = dispatcher.list_active()
        self.state.active_symbols = list(active.keys())

        for symbol in active.keys():
            if symbol in open_symbols:
                continue
            if len(self.state.open_positions) >= self.config.max_positions:
                break

            candles = await self._fetch_candles(symbol)
            if len(candles) < self.config.warmup_candles:
                continue

            try:
                decision = dispatcher.make_decision(symbol, candles)
            except Exception:
                continue

            if decision is None or not decision["should_trade"]:
                continue

            invest = self.state.capital * (self.config.position_size_pct / 100)
            invest = min(invest, self.state.capital * 0.9)
            if invest < 10_000:
                continue

            entry = decision["entry"]
            quantity = invest / entry

            pos = PaperPosition(
                symbol=symbol,
                strategy=decision["strategy"],
                entry_price=entry,
                quantity=quantity,
                tp=decision["tp"],
                sl=decision["sl"],
                entry_time=candles[-1].time,
                entry_idx=len(candles) - 1,
                reason=decision["reason"],
            )
            self.state.open_positions.append(asdict(pos))

    # ---------- Loop ----------
    async def _loop(self):
        while self.state.is_running:
            try:
                self.state.last_check_time = int(time.time())
                await self._check_exits()
                await self._check_entries()
                self.save_state()
            except Exception as e:
                print(f"⚠️ Paper V2 error: {e}")

            await asyncio.sleep(self.config.check_interval_sec)

    # ---------- API ----------
    async def start(self, exchange: ExchangePort):
        if self.state.is_running:
            return {"status": "already_running"}

        self._exchange = exchange

        # بازیابی اگر قبلاً ران بود
        if not self.state.open_positions and self.state.total_trades == 0:
            self.load_state()

        self.state.is_running = True
        if self.state.started_at == 0:
            self.state.started_at = int(time.time())
        self._task = asyncio.create_task(self._loop())
        return {"status": "started", "active_symbols": list(dispatcher.list_active().keys())}

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
        if TRADES_FILE.exists():
            TRADES_FILE.unlink()
        return {"status": "reset"}

    def get_status(self) -> dict:
        s = self.state
        wr = (s.wins / s.total_trades * 100) if s.total_trades > 0 else 0
        ret = (s.capital - s.initial_capital) / s.initial_capital * 100
        runtime_min = (int(time.time()) - s.started_at) // 60 if s.started_at else 0
        return {
            "is_running": s.is_running,
            "started_at": s.started_at,
            "runtime_minutes": runtime_min,
            "initial_capital": s.initial_capital,
            "current_capital": round(s.capital, 1),
            "total_return_pct": round(ret, 2),
            "profit_tmn": round(s.capital - s.initial_capital, 1),
            "max_drawdown_pct": round(s.max_drawdown_pct, 2),
            "total_trades": s.total_trades,
            "wins": s.wins,
            "losses": s.losses,
            "win_rate": round(wr, 2),
            "open_positions": s.open_positions,
            "recent_trades": s.recent_trades[:20],
            "equity_curve": s.equity_curve[-100:],
            "last_check_time": s.last_check_time,
            "active_symbols": s.active_symbols,
            "config": asdict(self.config),
        }


paper_trader_v2 = PaperTraderV2()
