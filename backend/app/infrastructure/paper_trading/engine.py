"""Paper Trading Engine — موتور اصلی."""

import asyncio
import time
from pathlib import Path

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
        state_dir: Path | None = None,
    ):
        self.exchange = exchange
        self.bot_slug = bot_slug
        self.symbols = symbols
        self.timeframe = timeframe
        self.position_size_pct = position_size_pct
        self.fee_pct = fee_pct
        self.check_interval_sec = check_interval_sec

        self.repo = (
            PaperRepository(state_dir=state_dir)
            if state_dir is not None
            else PaperRepository()
        )
        # چک: state قبلاً ذخیره شده یا نه
        state_exists = self.repo.state_file.exists()
        self.state = self.repo.load()
        if not state_exists:
            # state جدید — با initial_capital شروع کن
            self.state.initial_capital = initial_capital
            self.state.capital = initial_capital
            self.state.equity = initial_capital
            self.state.peak_capital = initial_capital
            self.state.peak_equity = initial_capital
        else:
            # state قدیمی — فقط initial_capital رو آپدیت کن
            self.state.initial_capital = initial_capital

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

    async def execute_manual_order(
        self,
        side: str,
        symbol: str,
        quantity: float = 0.0,
        amount_tmn: float = 0.0,
        limit_price: float = 0.0,
        tp_pct: float = 2.0,
        sl_pct: float = 1.0,
    ) -> dict:
        """سفارش دستی مهمان (شبیه‌سازی).

        Args:
            side: "buy" یا "sell"
            symbol: نماد
            quantity: مقدار
            tp_pct: درصد سود (پیش‌فرض ۲٪)
            sl_pct: درصد ضرر (پیش‌فرض ۱٪)

        Returns:
            dict: {status, position, error?}
        """
        # ── چک‌ها ──
        if side not in ("buy", "sell"):
            return {"status": "error", "error": "side باید buy یا sell باشه"}

        if quantity <= 0 and amount_tmn <= 0:
            return {"status": "error", "error": "quantity یا amount_tmn لازم است"}

        if len(self.state.open_positions) >= 10:
            return {"status": "error", "error": "سقف ۱۰ پوزیشن باز"}

        if any(p["symbol"] == symbol for p in self.state.open_positions):
            return {"status": "error", "error": f"{symbol} قبلاً باز است"}

        # ── قیمت لحظه‌ای ──
        try:
            uc = GetCandlesUseCase(exchange=self.exchange)
            candles = await uc.execute(symbol=symbol, timeframe=self.timeframe, limit=2)
            if not candles:
                return {"status": "error", "error": "قیمت دریافت نشد"}
            price = float(candles[-1].close)
        except Exception as e:
            return {"status": "error", "error": f"خطا: {e}"}

        # ── چک limit_price (شبیه‌سازی Limit Order) ──
        if limit_price > 0:
            if side == "buy" and limit_price < price:
                return {
                    "status": "error",
                    "error": (
                        f"قیمت پیشنهادی شما ({limit_price:,.0f}) از قیمت بازار "
                        f"({price:,.0f}) پایین‌تره. برای خرید، قیمت باید ≥ بازار باشه."
                    ),
                }
            if side == "sell" and limit_price > price:
                return {
                    "status": "error",
                    "error": (
                        f"قیمت پیشنهادی شما ({limit_price:,.0f}) از قیمت بازار "
                        f"({price:,.0f}) بالاترـه. برای فروش، قیمت باید ≤ بازار باشه."
                    ),
                }

        # ── محاسبه‌ی quantity از amount_tmn (اگه کاربر مبلغ داده) ──
        if amount_tmn > 0 and quantity <= 0:
            quantity = amount_tmn / price

        if quantity <= 0:
            return {"status": "error", "error": "quantity نامعتبر"}

        # ── محاسبه‌ی هزینه ──
        cost = price * quantity
        if cost > self.state.capital:
            return {
                "status": "error",
                "error": f"سرمایه کافی نیست (نیاز: {cost:.0f}، موجود: {self.state.capital:.0f})",
            }

        # ── SL/TP ──
        if side == "buy":
            tp = price * (1 + tp_pct / 100)
            sl = price * (1 - sl_pct / 100)
        else:  # sell (short)
            tp = price * (1 - tp_pct / 100)
            sl = price * (1 + sl_pct / 100)

        # ── ساخت پوزیشن ──
        pos = {
            "symbol": symbol,
            "side": side,
            "entry_price": price,
            "current_price": price,
            "quantity": quantity,
            "cost": cost,
            "tp": tp,
            "sl": sl,
            "tp_pct": tp_pct,
            "sl_pct": sl_pct,
            "entry_time": int(time.time()),
            "source": "manual",
        }

        # ── آپدیت state ──
        self.state.open_positions.append(pos)
        self.state.capital -= cost
        self.state.total_trades += 1
        self.state.update_metrics()

        self._log_event(
            "manual_order",
            f"سفارش دستی: {side} {symbol} @ {price:,.0f}",
            symbol=symbol,
            data={"side": side, "quantity": quantity, "price": price},
        )

        self.repo.save(self.state)

        return {"status": "ok", "position": pos}

    async def close_position(self, symbol: str) -> dict:
        """بستن دستی پوزیشن."""
        for pos in list(self.state.open_positions):
            if pos["symbol"] == symbol:
                try:
                    uc = GetCandlesUseCase(exchange=self.exchange)
                    candles = await uc.execute(symbol=symbol, timeframe=self.timeframe, limit=2)
                    exit_price = float(candles[-1].close) if candles else pos["current_price"]
                except Exception:
                    exit_price = pos["current_price"]

                self._close_position(pos, exit_price, "manual_close")
                self.state.open_positions.remove(pos)
                self.state.update_metrics()
                self.repo.save(self.state)

                self._log_event(
                    "manual_close",
                    f"بستن دستی: {symbol} @ {exit_price:,.0f}",
                    symbol=symbol,
                )
                return {"status": "ok", "exit_price": exit_price}

        return {"status": "error", "error": f"پوزیشن {symbol} پیدا نشد"}

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
                # فقط کندل‌های بسته؛ کندل جاری ناتمام است (هم‌رفتار با بک‌تست)
                if candles:
                    from app.application.use_cases.get_candles import TIMEFRAME_MAP
                    tf_sec = TIMEFRAME_MAP.get(self.timeframe, ("", 1, 3600))[2]
                    if candles[-1].time + tf_sec > int(time.time()):
                        candles = candles[:-1]
                if not candles:
                    self._log_event("error", "کندلی دریافت نشد", symbol=symbol)
                    continue
                scanned += 1

                checks = bot.diagnose(symbol, candles) if hasattr(bot, "diagnose") else []
                core = [c for c in checks if c["name"] in ("liquidity", "drop", "green", "rsi", "body")]
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
