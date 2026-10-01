"""Historical Replay Bot — شبیه‌سازی روی داده‌ی گذشته.

مثل Paper Trader کار می‌کنه ولی روی گذشته:
  - یک بازه‌ی تاریخی می‌گیره (مثلاً 1 Aug - 31 Aug)
  - کندل‌ها رو به ترتیب زمانی replay می‌کنه
  - با سرعت قابل تنظیم (30x، 60x، 300x)
  - state و تریدها رو جدا ذخیره می‌کنه
"""

from __future__ import annotations

import asyncio
import contextlib
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from app.domain.entities.candle import Candle
from app.domain.ports.exchange import ExchangePort
from app.services.bottom_detector import detect_bottom
from app.services.ml_bottom_model import build_features, candles_to_df, load_model
from app.services.scalping_strategy import STOP_LOSS_PCT, TAKE_PROFIT_PCT

STATE_DIR = Path("data/replay")
STATE_FILE = STATE_DIR / "state.json"
TRADES_FILE = STATE_DIR / "trades.jsonl"


@dataclass
class ReplayPosition:
    symbol: str
    entry_price: float
    quantity: float
    tp: float
    sl: float
    entry_time: int
    entry_candle_index: int
    ml_prob: float | None
    rule_score: int
    reason: str


@dataclass
class ReplayTrade:
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
class ReplayState:
    is_running: bool = False
    is_finished: bool = False
    mode: str = "replay"  # یا "step"
    start_date: str = ""
    end_date: str = ""
    speed: int = 60
    current_candle_time: int = 0
    progress_pct: float = 0.0
    processed_candles: int = 0
    total_candles: int = 0
    initial_capital: float = 300_000.0
    capital: float = 300_000.0
    peak_capital: float = 300_000.0
    max_drawdown_pct: float = 0.0
    total_trades: int = 0
    wins: int = 0
    losses: int = 0
    open_positions: list[dict[str, Any]] = field(default_factory=list)
    recent_trades: list[dict[str, Any]] = field(default_factory=list)
    equity_curve: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class ReplayConfig:
    symbols: list[str] = field(
        default_factory=lambda: ["BTCTMN", "ETHTMN", "XRPTMN", "DOGETMN", "SOLTMN"]
    )
    timeframe: str = "15m"
    start_date: str = "2026-09-01"
    end_date: str = "2026-09-30"
    speed: int = 60  # 60x = 1 ساعت کندل در 1 دقیقه واقعی
    max_positions: int = 2
    capital_per_position_pct: float = 0.5
    ml_threshold: float = 0.55
    rule_min_score: int = 5
    warmup_candles: int = 100
    max_duration_candles: int = 24
    fee_pct: float = 0.2
    initial_capital: float = 300_000.0


class HistoricalReplayBot:
    def __init__(self):
        self.config = ReplayConfig()
        self.state = ReplayState()
        self._task: asyncio.Task | None = None
        self._model = None
        self._exchange: ExchangePort | None = None

    # ---------- Persistence ----------
    def _ensure_dir(self):
        STATE_DIR.mkdir(parents=True, exist_ok=True)

    def save_state(self):
        self._ensure_dir()
        STATE_FILE.write_text(json.dumps(asdict(self.state), indent=2, default=str))

    def append_trade(self, trade: ReplayTrade):
        self._ensure_dir()
        with TRADES_FILE.open("a") as f:
            f.write(json.dumps(asdict(trade), default=str) + "\n")

    # ---------- Data ----------
    async def _fetch_range(self, symbol: str) -> list[Candle]:
        """دریافت کندل در بازه‌ی تاریخ مشخص."""
        from datetime import datetime

        if self._exchange is None:
            return []

        try:
            start_dt = datetime.strptime(self.config.start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(self.config.end_date, "%Y-%m-%d")
            start_ts = int(start_dt.timestamp())
            end_ts = int(end_dt.timestamp()) + 86400

            # نگاشت TF به resolution والکس
            tf_map = {"15m": "15", "1h": "60", "4h": "60", "1D": "D"}
            resolution = tf_map.get(self.config.timeframe, "15")

            # اگه 4h بود، بعداً aggregate می‌کنیم
            raw = await self._exchange.get_candles(
                symbol=symbol,
                resolution=resolution,
                from_ts=start_ts,
                to_ts=end_ts,
            )
            return raw
        except Exception as e:
            print(f"❌ fetch {symbol}: {e}")
            return []

    async def _preload_all_data(self) -> dict[str, list[Candle]]:
        """دریافت موازی همه‌ی نمادها."""
        tasks = [self._fetch_range(sym) for sym in self.config.symbols]
        results = await asyncio.gather(*tasks)
        return {sym: candles for sym, candles in zip(self.config.symbols, results) if candles}

    # ---------- Model ----------
    def _load_model(self):
        if self._model is None:
            with contextlib.suppress(FileNotFoundError):
                self._model = load_model()

    def _predict_ml_from_slice(self, candles_slice: list[Candle]) -> float | None:
        if self._model is None or len(candles_slice) < self.config.warmup_candles:
            return None
        try:
            df = candles_to_df(candles_slice)
            X = build_features(df)
            last = X.iloc[[-1]]
            if last.isna().any(axis=1).iloc[0]:
                return None
            prob = self._model.predict_proba(last)[0]
            return float(prob[1])
        except Exception:
            return None

    # ---------- Replay Logic ----------
    def _check_exit(
        self, pos_data: dict, candle: Candle, current_idx: int
    ) -> tuple[float | None, str]:
        """بررسی خروج روی یک کندل."""
        pos = ReplayPosition(**pos_data)
        # TP
        if candle.high >= pos.tp:
            return pos.tp, "take_profit"
        # SL
        if candle.low <= pos.sl:
            return pos.sl, "stop_loss"
        # Timeout
        if (current_idx - pos.entry_candle_index) >= self.config.max_duration_candles:
            return float(candle.close), "timeout"
        return None, ""

    def _close_position(self, pos_data: dict, exit_price: float, reason: str, candle: Candle):
        pos = ReplayPosition(**pos_data)
        pnl_pct = (exit_price / pos.entry_price - 1) * 100 - self.config.fee_pct
        pnl_tmn = (exit_price - pos.entry_price) * pos.quantity
        # کسر کارمزد کامل
        fees = (pos.quantity * pos.entry_price + pos.quantity * exit_price) * (
            self.config.fee_pct / 200
        )
        pnl_tmn -= fees

        self.state.capital += pnl_tmn
        if self.state.capital > self.state.peak_capital:
            self.state.peak_capital = self.state.capital
        dd = (self.state.peak_capital - self.state.capital) / self.state.peak_capital * 100
        if dd > self.state.max_drawdown_pct:
            self.state.max_drawdown_pct = dd

        if pnl_pct > 0:
            self.state.wins += 1
        else:
            self.state.losses += 1
        self.state.total_trades += 1

        trade = ReplayTrade(
            symbol=pos.symbol,
            entry_time=pos.entry_time,
            exit_time=candle.time,
            entry_price=pos.entry_price,
            exit_price=exit_price,
            quantity=pos.quantity,
            pnl_pct=pnl_pct,
            pnl_tmn=pnl_tmn,
            exit_reason=reason,
            duration_candles=0,
            ml_prob=pos.ml_prob,
            rule_score=pos.rule_score,
        )
        self.append_trade(trade)
        self.state.recent_trades.insert(0, asdict(trade))
        self.state.recent_trades = self.state.recent_trades[:50]
        self.state.equity_curve.append(
            {
                "time": candle.time,
                "capital": round(self.state.capital, 1),
            }
        )

    # ---------- Main Replay Loop ----------
    async def _replay_loop(self, markets_data: dict[str, list[Candle]]):
        """حلقه‌ی اصلی replay."""
        # ساخت لیست همه‌ی کندل‌ها بر اساس زمان
        all_events: list[tuple[int, str, Candle, int]] = []
        for symbol, candles in markets_data.items():
            for i, c in enumerate(candles):
                all_events.append((c.time, symbol, c, i))
        all_events.sort(key=lambda x: x[0])

        self.state.total_candles = len(all_events)
        self.state.processed_candles = 0

        # داده‌های هر نماد به صورت rolling برای ML
        symbol_candles: dict[str, list[Candle]] = {s: [] for s in markets_data}

        for event_time, symbol, candle, symbol_idx in all_events:
            if not self.state.is_running:
                break

            # بدون تاخیر — سریع‌ترین حالت
            # هر 100 کندل یه بار اجازه می‌دیم event loop نفس بکشه
            if self.state.processed_candles % 100 == 0:
                await asyncio.sleep(0)

            # اضافه کردن کندل به window
            symbol_candles[symbol].append(candle)
            if len(symbol_candles[symbol]) > 300:
                symbol_candles[symbol] = symbol_candles[symbol][-300:]

            self.state.current_candle_time = event_time
            self.state.processed_candles += 1
            self.state.progress_pct = round(
                self.state.processed_candles / self.state.total_candles * 100, 2
            )

            # ---- ۱. چک خروج ----
            positions_to_remove = []
            for i, pos_data in enumerate(self.state.open_positions):
                if pos_data["symbol"] != symbol:
                    continue
                exit_price, reason = self._check_exit(pos_data, candle, symbol_idx)
                if exit_price is not None:
                    self._close_position(pos_data, exit_price, reason, candle)
                    positions_to_remove.append(i)

            for i in reversed(positions_to_remove):
                self.state.open_positions.pop(i)

            # ---- ۲. چک ورود ----
            if len(self.state.open_positions) < self.config.max_positions:
                open_syms = {p["symbol"] for p in self.state.open_positions}
                if symbol not in open_syms:
                    window = symbol_candles[symbol]
                    if len(window) >= self.config.warmup_candles:
                        ml_prob = self._predict_ml_from_slice(window)
                        rule = detect_bottom(window)

                        ml_ok = ml_prob is not None and ml_prob >= self.config.ml_threshold
                        rule_ok = rule.is_bottom and rule.score >= self.config.rule_min_score

                        if ml_ok or rule_ok:
                            entry = float(candle.close)
                            cap_per = (
                                self.state.initial_capital * self.config.capital_per_position_pct
                            )
                            invest = min(cap_per, self.state.capital * 0.9)
                            if invest >= 10_000:
                                qty = invest / entry
                                tp = entry * (1 + float(TAKE_PROFIT_PCT) / 100)
                                sl = entry * (1 - float(STOP_LOSS_PCT) / 100)

                                reasons = []
                                if ml_ok:
                                    reasons.append(f"ML={ml_prob:.2f}")
                                if rule_ok:
                                    reasons.append(f"score={rule.score}")

                                self.state.open_positions.append(
                                    asdict(
                                        ReplayPosition(
                                            symbol=symbol,
                                            entry_price=entry,
                                            quantity=qty,
                                            tp=tp,
                                            sl=sl,
                                            entry_time=candle.time,
                                            entry_candle_index=symbol_idx,
                                            ml_prob=ml_prob,
                                            rule_score=rule.score,
                                            reason=" | ".join(reasons),
                                        )
                                    )
                                )

            # ذخیره‌ی دوره‌ای
            if self.state.processed_candles % 100 == 0:
                self.save_state()

        # پایان
        self.state.is_running = False
        self.state.is_finished = True
        self.save_state()

    # ---------- Public API ----------
    async def start(self, exchange: ExchangePort, config: dict | None = None):
        """شروع replay."""
        if self.state.is_running:
            return {"status": "already_running"}

        # اعمال تنظیمات
        if config:
            for key, val in config.items():
                if hasattr(self.config, key) and val is not None:
                    setattr(self.config, key, val)

        self._exchange = exchange
        self._load_model()

        # ریست state
        self.state = ReplayState(
            is_running=True,
            mode="replay",
            start_date=self.config.start_date,
            end_date=self.config.end_date,
            speed=self.config.speed,
            initial_capital=self.config.initial_capital,
            capital=self.config.initial_capital,
            peak_capital=self.config.initial_capital,
        )

        # پاک کردن فایل‌های قبلی
        self._ensure_dir()
        if TRADES_FILE.exists():
            TRADES_FILE.unlink()

        # پیش‌بارگذاری داده
        print("📥 Fetching historical data...")
        markets_data = await self._preload_all_data()
        if not markets_data:
            self.state.is_running = False
            return {"status": "error", "message": "داده‌ای یافت نشد"}

        print(f"✅ {len(markets_data)} نماد دریافت شد")

        # شروع حلقه
        self._task = asyncio.create_task(self._replay_loop(markets_data))
        return {
            "status": "started",
            "symbols_loaded": list(markets_data.keys()),
            "total_candles": sum(len(c) for c in markets_data.values()),
        }

    async def stop(self):
        self.state.is_running = False
        if self._task:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
        self.save_state()
        return {"status": "stopped"}

    def reset(self):
        self.state = ReplayState()
        self.save_state()
        if TRADES_FILE.exists():
            TRADES_FILE.unlink()
        return {"status": "reset"}

    def get_status(self) -> dict:
        s = self.state
        win_rate = (s.wins / s.total_trades * 100) if s.total_trades > 0 else 0
        ret_pct = (s.capital - s.initial_capital) / s.initial_capital * 100
        return {
            "is_running": s.is_running,
            "is_finished": s.is_finished,
            "date_range": f"{s.start_date} → {s.end_date}",
            "speed": s.speed,
            "progress_pct": s.progress_pct,
            "processed_candles": s.processed_candles,
            "total_candles": s.total_candles,
            "current_candle_time": s.current_candle_time,
            "initial_capital": s.initial_capital,
            "current_capital": round(s.capital, 1),
            "total_return_pct": round(ret_pct, 2),
            "max_drawdown_pct": round(s.max_drawdown_pct, 2),
            "total_trades": s.total_trades,
            "wins": s.wins,
            "losses": s.losses,
            "win_rate": round(win_rate, 2),
            "open_positions": s.open_positions,
            "recent_trades": s.recent_trades[:20],
            "equity_curve": s.equity_curve[-200:],
            "config": asdict(self.config),
        }


# Singleton جدا از paper_trader
replay_bot = HistoricalReplayBot()
