"""NooaahRunner — orchestrator: bot + executor + state.

هر cycle (~۱ ساعت):
  ۱. reset روزانه اگه لازم
  ۲. اگه killed یا daily_loss_hit → هیچ کاری
  ۳. مدیریت پوزیشن‌های باز (چک TP/SL/timeout)
  ۴. اگه جا هست → proposal جدید بگیر + اجرا
  ۵. ذخیره state
"""

from __future__ import annotations

import time
import uuid
from dataclasses import asdict
from pathlib import Path

import structlog

from app.domain.ports.exchange import ExchangePort
from app.services.bots.nooaah.bot import NooaahBot
from app.services.bots.nooaah.config import NooaahConfig
from app.services.bots.nooaah.executor import (
    Executor,
    LiveExecutor,
    PaperExecutor,
)
from app.services.bots.nooaah.state import (
    STATE_FILE,
    NooaahClosedTrade,
    NooaahPosition,
    NooaahState,
)

log = structlog.get_logger("nooaah.runner")

FEE_PCT = 0.2  # مطابق backtest


class NooaahRunner:
    """چرخه‌ی کامل ربات: analyze → decide → execute → persist."""

    def __init__(
        self,
        exchange: ExchangePort,
        config: NooaahConfig | None = None,
        capital_total: float | None = None,
        state_path: Path | None = None,
    ) -> None:
        self._exchange = exchange
        self._config = config or NooaahConfig()
        self._bot = NooaahBot(exchange=exchange, config=self._config)
        self._state_path = state_path or STATE_FILE
        self._state = NooaahState.load(self._state_path)

        # اگه سرمایه داده شد و state خالی بود → init
        if capital_total is not None and self._state.capital_total == 0:
            self._state.capital_total = capital_total
            self._state.capital_available = capital_total
            self._state.save(self._state_path)

    # ---------- Properties ----------
    @property
    def state(self) -> NooaahState:
        return self._state

    def _executor(self) -> Executor:
        if self._state.mode == "live":
            return LiveExecutor(self._exchange)
        return PaperExecutor(self._exchange)

    # ============================================================
    # Main cycle
    # ============================================================
    async def run_cycle(self) -> dict:
        """یه چرخه‌ی کامل. return: خلاصه."""
        t0 = time.monotonic()
        self._state.reset_daily_if_needed()

        if self._state.killed:
            return self._summary(t0, status="killed")

        if self._state.daily_loss_hit:
            # ممکنه cooldown فعال یا تموم شده
            if self._state.cooldown_remaining_seconds > 0:
                return self._summary(
                    t0, status="cooldown",
                    error=f"cooldown: {self._state.cooldown_remaining_seconds}s remaining",
                )
            # cooldown تموم شد → پاک‌سازی
            self._state.daily_loss_hit = False
            self._state.cooldown_until = 0

        if self._state.capital_total <= 0:
            return self._summary(
                t0, status="no_capital",
                error="capital_total=0 — allocate from wallet first",
            )

        # ۱. مدیریت پوزیشن‌های باز
        closed = await self._manage_open_positions()

        # ۲. اگه جا هست → proposal جدید
        opened = None
        if len(self._state.open_positions) < self._config.max_concurrent_positions:
            opened = await self._try_open_new()

        self._state.last_run = int(time.time())
        self._state.save(self._state_path)

        return self._summary(
            t0, status="ok", closed=closed, opened=opened,
        )

    # ============================================================
    # Position management
    # ============================================================
    async def _manage_open_positions(self) -> list[dict]:
        """چک TP/SL/timeout برای هر پوزیشن باز."""
        executor = self._executor()
        closed: list[dict] = []
        still_open: list[NooaahPosition] = []

        for pos in self._state.open_positions:
            try:
                price = await executor.get_current_price(pos.symbol)
            except Exception as exc:
                log.warning(
                    "nooaah.price_fetch_failed",
                    symbol=pos.symbol, error=str(exc),
                )
                still_open.append(pos)
                continue

            exit_price: float | None = None
            reason = ""
            duration_h = (int(time.time()) - pos.entry_time) / 3600

            if price <= pos.sl:
                exit_price = pos.sl
                reason = "stop_loss"
            elif price >= pos.tp:
                exit_price = pos.tp
                reason = "take_profit"
            elif duration_h >= self._config.max_duration_hours:
                exit_price = price
                reason = "timeout"

            if exit_price is None:
                still_open.append(pos)
                continue

            # بستن
            ret_pct = (exit_price / pos.entry_price - 1) * 100 - FEE_PCT
            pnl = pos.capital_used * ret_pct / 100.0

            trade = NooaahClosedTrade(
                client_id=pos.client_id,
                symbol=pos.symbol,
                entry_price=pos.entry_price,
                exit_price=exit_price,
                quantity=pos.quantity,
                entry_time=pos.entry_time,
                exit_time=int(time.time()),
                exit_reason=reason,
                return_pct=round(ret_pct, 4),
                pnl=round(pnl, 2),
                duration_candles=int(duration_h),
                confidence=pos.confidence,
                mode=self._state.mode,
            )
            self._state.closed_trades.append(trade)
            closed.append(asdict(trade))

            # آپدیت سرمایه
            self._state.capital_available += pos.capital_used + pnl
            self._state.capital_in_use -= pos.capital_used
            self._state.daily_pnl_pct += ret_pct * pos.size_mult

            log.info(
                "nooaah.position_closed",
                symbol=pos.symbol,
                reason=reason,
                ret_pct=round(ret_pct, 2),
                pnl=round(pnl, 2),
            )

        self._state.open_positions = still_open

        # چک daily loss → cooldown ۶ ساعته (ADR-0013)
        if self._state.daily_pnl_pct <= -self._state.daily_loss_limit_pct:
            if not self._state.daily_loss_hit:
                self._state.enter_cooldown(hours=6)
                log.warning(
                    "nooaah.daily_loss_hit_cooldown",
                    pnl_pct=round(self._state.daily_pnl_pct, 2),
                    limit=self._state.daily_loss_limit_pct,
                    cooldown_until=self._state.cooldown_until,
                )

        return closed

    # ============================================================
    # New position
    # ============================================================
    async def _try_open_new(self) -> dict | None:
        """اگه proposal هست و شرایط OK، پوزیشن جدید باز کن."""
        result = await self._bot.run_once()
        if result.proposal is None:
            return None

        p = result.proposal

        # skip نماد تکراری
        if self._state.has_position_for(p.symbol):
            return None

        # محاسبه‌ی حجم
        capital_to_use = self._state.capital_available * 0.95  # ۵٪ buffer
        if capital_to_use <= 0:
            return None

        entry_price = p.entry
        if entry_price <= 0:
            return None

        quantity = capital_to_use / entry_price

        # client_id یکتا
        client_id = (
            f"nooaah_{int(time.time())}_{p.symbol}_{uuid.uuid4().hex[:6]}"
        )

        # اجرا
        executor = self._executor()
        try:
            order = await executor.place_market_buy(
                symbol=p.symbol,
                quantity=__import__("decimal").Decimal(str(quantity)),
                client_id=client_id,
            )
        except Exception as exc:
            log.error(
                "nooaah.execute_failed",
                symbol=p.symbol, error=str(exc),
            )
            return None

        # ثبت در state
        pos = NooaahPosition(
            client_id=client_id,
            symbol=p.symbol,
            entry_price=entry_price,
            quantity=quantity,
            tp=p.take_profit,
            sl=p.stop_loss,
            entry_time=int(time.time()),
            confidence=p.confidence,
            size_mult=p.size_mult,
            capital_used=capital_to_use,
        )
        self._state.open_positions.append(pos)
        self._state.capital_available -= capital_to_use
        self._state.capital_in_use += capital_to_use

        log.info(
            "nooaah.position_opened",
            symbol=p.symbol,
            entry=entry_price,
            tp=p.take_profit,
            sl=p.stop_loss,
            confidence=p.confidence,
            client_id=client_id,
            mode=self._state.mode,
            order_status=order.status.value if hasattr(order, "status") else "?",
        )
        return asdict(pos)

    # ============================================================
    # Stop logic (ADR-0013)
    # ============================================================
    async def preview_stop(self) -> dict:
        """پیش‌نمایش: پوزیشن‌های باز + قیمت فعلی + PnL. بدون تغییر state."""
        executor = self._executor()
        positions_info: list[dict] = []
        for pos in self._state.open_positions:
            try:
                bid = await executor.get_best_bid(pos.symbol)
                last = await executor.get_current_price(pos.symbol)
            except Exception:
                bid = last = pos.entry_price
            pnl_pct = (bid / pos.entry_price - 1) * 100 if pos.entry_price else 0.0
            pnl_abs = pos.capital_used * pnl_pct / 100.0
            positions_info.append({
                "client_id": pos.client_id,
                "symbol": pos.symbol,
                "entry_price": pos.entry_price,
                "entry_time": pos.entry_time,
                "quantity": pos.quantity,
                "capital_used": pos.capital_used,
                "best_bid": bid,
                "last_price": last,
                "pnl_pct": round(pnl_pct, 3),
                "pnl_abs": round(pnl_abs, 2),
                "confidence": pos.confidence,
            })

        total_pnl_abs = sum(p["pnl_abs"] for p in positions_info)
        return {
            "mode": self._state.mode,
            "open_positions": positions_info,
            "count": len(positions_info),
            "total_pnl_abs": round(total_pnl_abs, 2),
            "capital_in_use": round(self._state.capital_in_use, 2),
        }

    async def stop_with_action(self, action: str) -> dict:
        """توقف با یکی از سه action:

        - 'sell': MARKET SELL همه‌ی پوزیشن‌ها → برگرداندن پول → live-paused
        - 'pause': پوزیشن‌ها باز بمونن → live-paused (قابل resume)
        - 'kill': پوزیشن‌ها باز بمونن → killed (غیرقابل resume)
        """
        if action not in ("sell", "pause", "kill"):
            raise ValueError(f"invalid action: {action}")

        if action == "sell":
            await self._sell_all_positions()

        # state transition
        if action == "kill":
            self._state.killed = True
            self._state.killed_at = int(time.time())
            self._state.kill_activations_7d += 1
            self._state.mode = "live-paused"
            self._state.pause_reason = "kill توسط کاربر"
        else:  # sell or pause
            self._state.mode = "live-paused"
            self._state.pause_reason = (
                "فروش همه‌ی پوزیشن‌ها" if action == "sell" else "توقف موقت توسط کاربر"
            )

        self._state.last_run = int(time.time())
        self._state.save(self._state_path)

        return {
            "action": action,
            "mode": self._state.mode,
            "killed": self._state.killed,
            "open_positions": len(self._state.open_positions),
            "capital_available": round(self._state.capital_available, 2),
            "capital_in_use": round(self._state.capital_in_use, 2),
        }

    async def _sell_all_positions(self) -> None:
        """فروش MARKET همه‌ی پوزیشن‌های باز با best_bid."""
        executor = self._executor()
        closed: list[dict] = []
        still_open: list[NooaahPosition] = []

        for pos in self._state.open_positions:
            try:
                bid = await executor.get_best_bid(pos.symbol)
            except Exception as exc:
                log.error(
                    "nooaah.sell_bid_failed",
                    symbol=pos.symbol, error=str(exc),
                )
                still_open.append(pos)
                continue

            try:
                order = await executor.place_market_sell(
                    symbol=pos.symbol,
                    quantity=__import__("decimal").Decimal(str(pos.quantity)),
                    client_id=f"{pos.client_id}_exit",
                )
            except Exception as exc:
                log.error(
                    "nooaah.sell_failed",
                    symbol=pos.symbol, client_id=pos.client_id,
                    error=str(exc),
                )
                still_open.append(pos)
                continue

            # ثبت trade بسته‌شده
            exit_price = float(order.executed_price or bid)
            ret_pct = (exit_price / pos.entry_price - 1) * 100 - FEE_PCT
            pnl = pos.capital_used * ret_pct / 100.0

            trade = NooaahClosedTrade(
                client_id=pos.client_id,
                symbol=pos.symbol,
                entry_price=pos.entry_price,
                exit_price=exit_price,
                quantity=pos.quantity,
                entry_time=pos.entry_time,
                exit_time=int(time.time()),
                exit_reason="manual_sell",
                return_pct=round(ret_pct, 4),
                pnl=round(pnl, 2),
                duration_candles=max(0, int((time.time() - pos.entry_time) / 3600)),
                confidence=pos.confidence,
                mode=self._state.mode,
            )
            self._state.closed_trades.append(trade)
            closed.append(asdict(trade))

            # پول برمی‌گرده
            self._state.capital_available += pos.capital_used + pnl
            self._state.capital_in_use -= pos.capital_used

            log.info(
                "nooaah.position_sold",
                symbol=pos.symbol, client_id=pos.client_id,
                ret_pct=round(ret_pct, 2), pnl=round(pnl, 2),
            )

        self._state.open_positions = still_open
        if closed:
            self._state.consecutive_losses = 0  # reset (چون کاربر دخالت کرده)

    # ============================================================
    # Summary
    # ============================================================
    def _summary(
        self,
        t0: float,
        status: str,
        closed: list[dict] | None = None,
        opened: dict | None = None,
        error: str | None = None,
    ) -> dict:
        return {
            "status": status,
            "mode": self._state.mode,
            "duration_seconds": round(time.monotonic() - t0, 2),
            "capital_total": self._state.capital_total,
            "capital_available": round(self._state.capital_available, 2),
            "capital_in_use": round(self._state.capital_in_use, 2),
            "open_positions": len(self._state.open_positions),
            "closed_trades_total": len(self._state.closed_trades),
            "daily_pnl_pct": round(self._state.daily_pnl_pct, 4),
            "closed_this_cycle": closed or [],
            "opened_this_cycle": opened,
            "error": error,
        }
