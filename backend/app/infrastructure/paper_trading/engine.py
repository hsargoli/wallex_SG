"""Paper Trading Engine — موتور اصلی."""

import asyncio
import time

from app.application.use_cases.get_candles import GetCandlesUseCase
from app.domain.ports.exchange import ExchangePort
from app.infrastructure.paper_trading.repository import PaperRepository
from app.infrastructure.paper_trading.state import PaperState
from app.services.bots import bot_registry


class PaperEngine:
    """موتور Paper Trading."""

    def __init__(
        self,
        exchange: ExchangePort,
        bot_slug: str,
        symbols: list[str],
        timeframe: str = "1h",
        initial_capital: float = 1000.0,
        check_interval_sec: int = 180,
        position_size_pct: float = 50.0,
        fee_pct: float = 0.2,
    ):
        self.exchange = exchange
        self.bot_slug = bot_slug
        self.symbols = symbols
        self.timeframe = timeframe
        self.position_size_pct = position_size_pct
        self.fee_pct = fee_pct
        self.check_interval_sec = check_interval_sec

        self.repo = PaperRepository()
        self.state = self.repo.load()
        self.state.initial_capital = initial_capital
        if self.state.capital == 0:
            self.state.capital = initial_capital
            self.state.peak_capital = initial_capital

        self._task: asyncio.Task | None = None

    async def start(self) -> dict:
        """شروع."""
        if self.state.is_running:
            return {"status": "already_running"}

        self.state.is_running = True
        self.state.started_at = int(time.time())

        # چک اول
        await self._check()

        # loop
        self._task = asyncio.create_task(self._loop())

        return {"status": "started", "bot_slug": self.bot_slug, "symbols": self.symbols}

    async def stop(self) -> dict:
        """توقف."""
        self.state.is_running = False
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        self.repo.save(self.state)
        return {"status": "stopped"}

    def reset(self) -> dict:
        """ریست."""
        self.state = PaperState(
            initial_capital=self.state.initial_capital,
            capital=self.state.initial_capital,
            equity=self.state.initial_capital,
            peak_capital=self.state.initial_capital,
            peak_equity=self.state.initial_capital,
        )
        self.repo.save(self.state)
        return {"status": "reset"}

    def get_status(self) -> dict:
        """وضعیت."""
        return self.state.to_dict()

    async def refresh_prices(self) -> None:
        """آپدیت قیمت لحظه‌ای برای همه پوزیشن‌های باز."""
        for pos in self.state.open_positions:
            try:
                uc = GetCandlesUseCase(exchange=self.exchange)
                candles = await uc.execute(
                    symbol=pos["symbol"],
                    timeframe=self.timeframe,
                    limit=2,
                )
                if candles:
                    pos["current_price"] = float(candles[-1].close)
            except Exception:
                pass
        self.state.update_metrics()

    async def _loop(self) -> None:
        """Loop اصلی."""
        while self.state.is_running:
            try:
                await asyncio.sleep(self.check_interval_sec)
                if not self.state.is_running:
                    break
                await self._check()
            except asyncio.CancelledError:
                break
            except Exception:
                await asyncio.sleep(60)

    async def _check(self) -> None:
        """چک همه نمادها."""
        bot = bot_registry.get(self.bot_slug)
        if bot is None:
            return

        # ۱. چک خروج پوزیشن‌های باز
        await self._check_exits()

        # ۲. چک ورود جدید
        await self._check_entries(bot)

        # ۳. آپدیت معیارها
        self.state.update_metrics()

        # ۴. ثبت equity curve در هر چک (برای نمودار زنده)
        self.state.equity_curve.append({
            "time": int(time.time()),
            "capital": round(self.state.equity, 2),
        })
        self.state.equity_curve = self.state.equity_curve[-500:]

        # ۵. ذخیره
        self.state.last_check_at = int(time.time())
        self.state.check_count += 1
        self.repo.save(self.state)

    async def _check_exits(self) -> None:
        """چک خروج."""
        remaining = []
        for pos in list(self.state.open_positions):
            symbol = pos["symbol"]
            try:
                uc = GetCandlesUseCase(exchange=self.exchange)
                candles = await uc.execute(symbol=symbol, timeframe=self.timeframe, limit=10)
                if not candles:
                    remaining.append(pos)
                    continue

                current = candles[-1]
                low = float(current.low)
                high = float(current.high)
                close = float(current.close)

                # آپدیت قیمت لحظه‌ای
                pos["current_price"] = close

                exit_price = None
                reason = None

                if low <= pos["sl"]:
                    exit_price = pos["sl"]
                    reason = "stop_loss"
                elif high >= pos["tp"]:
                    exit_price = pos["tp"]
                    reason = "take_profit"

                if exit_price:
                    self._close_position(pos, exit_price, reason)
                else:
                    remaining.append(pos)
            except Exception:
                remaining.append(pos)

        self.state.open_positions = remaining

    def _log_event(self, kind: str, message: str, symbol: str = "", data: dict | None = None, **extra) -> None:
        """ثبت رویداد (جدیدترین اول، سقف ۲۰۰)."""
        payload = dict(data or {})
        payload.update(extra)
        self.state.events.insert(0, {
            "time": int(time.time()),
            "kind": kind,
            "message": message,
            "symbol": symbol,
            "data": payload,
        })
        self.state.events = self.state.events[:200]

    async def _check_entries(self, bot) -> None:
        """چک ورود جدید + ثبت فکر ربات."""
        if len(self.state.open_positions) >= 3:  # حداکثر ۳ پوزیشن
            self._log_event("scan", "سقف ۳ پوزیشن باز پر است")
            return

        scanned = 0
        candidates = 0
        radar: list[dict] = []

        for symbol in self.symbols:
            if any(p["symbol"] == symbol for p in self.state.open_positions):
                continue

            try:
                uc = GetCandlesUseCase(exchange=self.exchange)
                candles = await uc.execute(symbol=symbol, timeframe=self.timeframe, limit=200)
                if not candles:
                    self._log_event("error", "کندلی دریافت نشد", symbol=symbol)
                    continue
                scanned += 1

                checks = bot.diagnose(symbol, candles) if hasattr(bot, "diagnose") else []
                core = [c for c in checks if c["name"] in ("drop", "green", "rsi", "body")]
                total = len(core)
                passed = sum(1 for c in core if c["passed"])
                if passed >= 2:
                    candidates += 1
                radar.append({
                    "symbol": symbol,
                    "passed": passed,
                    "total": total,
                    "pct": round(passed / total * 100) if total else 0,
                    "checks": checks,
                })

                decision = bot.make_decision(symbol, candles)
                ok = bool(decision and decision.get("should_trade"))

                if checks and (ok or passed >= 2 or len(self.symbols) <= 5):
                    self._log_event(
                        "think",
                        "شرایط ورود برقرار شد" if ok else "رد شد",
                        symbol=symbol,
                        data={"checks": checks, "decision": "enter" if ok else "skip"},
                    )

                if not ok:
                    continue

                self._log_event("signal", f"سیگنال: {decision.get('reason', '')}", symbol=symbol)
                self._open_position(symbol, decision)
            except Exception as exc:
                self._log_event("error", f"خطا: {type(exc).__name__}: {exc}", symbol=symbol)
                continue

        self.state.radar = radar
        self._log_event(
            "scan",
            f"اسکن {scanned} ارز ← {candidates} کاندید",
            data={"scanned": scanned, "candidates": candidates},
        )

    def _open_position(self, symbol: str, decision: dict) -> None:
        """باز کردن پوزیشن."""
        entry = float(decision["entry"])
        tp = float(decision["tp"])
        sl = float(decision["sl"])

        size_usd = self.state.capital * (self.position_size_pct / 100)
        fee_rate = self.fee_pct / 100
        entry_with_fee = entry * (1 + fee_rate)
        qty = size_usd / entry_with_fee

        self.state.capital -= size_usd

        self._log_event("enter", f"ورود: {qty:.4f} @ {entry_with_fee:.2f}", symbol=symbol)
        self.state.open_positions.append({
            "symbol": symbol,
            "side": "BUY",
            "entry_price": entry_with_fee,
            "quantity": qty,
            "tp": tp,
            "sl": sl,
            "entry_time": int(time.time()),
            "reason": decision.get("reason", ""),
            "bot_slug": self.bot_slug,
        })

    def _close_position(self, pos: dict, exit_price: float, reason: str) -> None:
        """بستن پوزیشن."""
        fee_rate = self.fee_pct / 100
        exit_with_fee = exit_price * (1 - fee_rate)

        qty = pos["quantity"]
        entry = pos["entry_price"]

        revenue = qty * exit_with_fee
        cost = qty * entry
        pnl = revenue - cost
        pnl_pct = (pnl / cost) * 100 if cost > 0 else 0

        self.state.capital += revenue
        self.state.total_trades += 1
        if pnl > 0:
            self.state.wins += 1
        else:
            self.state.losses += 1

        duration_min = (int(time.time()) - pos["entry_time"]) // 60

        trade = {
            "symbol": pos["symbol"],
            "side": pos["side"],
            "entry_time": pos["entry_time"],
            "exit_time": int(time.time()),
            "entry_price": entry,
            "exit_price": exit_with_fee,
            "quantity": qty,
            "pnl": round(pnl, 4),
            "pnl_pct": round(pnl_pct, 2),
            "exit_reason": reason,
            "duration_minutes": duration_min,
            "bot_slug": self.bot_slug,
        }
        self.state.recent_trades.insert(0, trade)
        self.state.recent_trades = self.state.recent_trades[:50]

        self._log_event(
            "win" if pnl > 0 else "exit",
            f"بستن: {reason} | PnL: {pnl_pct:+.2f}%",
            symbol=pos["symbol"],
        )

        # equity curve در _check ثبت می‌شود
