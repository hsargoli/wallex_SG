"""Worker تعقیب بهترین قیمت. پیش‌فرض dry-run است و فقط لاگ می‌کند."""
from __future__ import annotations

import asyncio
import logging
import time
import uuid
from collections import deque
from dataclasses import dataclass
from decimal import ROUND_FLOOR, Decimal
from typing import Any, Callable

from app.domain.entities.order import OrderRequest
from app.domain.value_objects.order_enums import OrderSide, OrderType
from app.services.order_chase.logic import Action, Level, decide

log = logging.getLogger("order_chase")


def _levels(raw: Any) -> list[Level]:
    out: list[Level] = []
    for lv in raw or []:
        try:
            if isinstance(lv, dict):
                p, q = lv.get("price"), lv.get("quantity")
            elif isinstance(lv, (list, tuple)):
                p, q = lv[0], lv[1]
            else:
                p, q = getattr(lv, "price", None), getattr(lv, "quantity", None)
            out.append((Decimal(str(p)), Decimal(str(q))))
        except Exception:
            continue
    return out


def floor_step(q: Decimal, step: Decimal | None) -> Decimal:
    if not step or step <= 0:
        return q
    return (q / step).to_integral_value(ROUND_FLOOR) * step


@dataclass
class ChaseConfig:
    symbol: str
    side: str
    low: Decimal
    high: Decimal
    quantity: Decimal
    interval_sec: int = 60
    dry_run: bool = True
    max_moves: int = 200
    max_notional: Decimal | None = None
    enforce_bound: bool = False
    deadline_sec: int = 6 * 3600
    min_move_ticks: int = 1
    max_errors: int = 3


@dataclass
class _Own:
    client_id: str
    price: Decimal
    qty: Decimal
    executed: Decimal = Decimal(0)


def validate_market(cfg: ChaseConfig, market: Any) -> str | None:
    q = floor_step(cfg.quantity, getattr(market, "step_size", None))
    mq = getattr(market, "min_quantity", None)
    mn = getattr(market, "min_notional", None)
    if q <= 0:
        return "مقدار پس از گرد کردن به step صفر می‌شود"
    if mq and q < mq:
        return f"مقدار کمتر از حداقل مجاز ({mq}) است"
    if mn and q * cfg.low < mn:
        return f"ارزش سفارش کمتر از حداقل مجاز ({mn}) است"
    return None


class ChaseWorker:
    def __init__(self, cfg: ChaseConfig, exchange: Any, can_trade: Callable[[], bool], market: Any = None):
        self.cfg = cfg
        self.ex = exchange
        self.can_trade = can_trade
        self.market = market
        self.id = uuid.uuid4().hex[:6]
        self.status = "running"
        self.started_at = int(time.time())
        self.deadline_at = self.started_at + cfg.deadline_sec
        self.own: _Own | None = None
        self.filled = Decimal(0)
        self.moves = 0
        self.errors = 0
        self.seq = 0
        self.last_action = ""
        self.last_reason = ""
        self.log: deque[dict] = deque(maxlen=200)
        self._last_key: tuple | None = None
        self._stop = False
        self._wake = asyncio.Event()
        self._task: asyncio.Task | None = None

    # ---------- کمکی ----------
    def _note(self, msg: str) -> None:
        self.log.append({"t": int(time.time()), "msg": msg})

    def _tick(self) -> Decimal:
        t = getattr(self.market, "tick_size", None)
        if t and t > 0:
            return Decimal(t)
        qp = getattr(self.market, "quote_precision", None)
        if isinstance(qp, int):
            return Decimal(1).scaleb(-qp)
        raise ValueError("tick_size نامشخص است")

    def _need(self) -> Decimal:
        return self.cfg.quantity - self.filled - (self.own.executed if self.own else Decimal(0))

    def _dust(self, q: Decimal) -> bool:
        q = floor_step(q, getattr(self.market, "step_size", None))
        mq = getattr(self.market, "min_quantity", None)
        return q <= 0 or bool(mq and q < mq)

    def _done(self, msg: str) -> None:
        self._note(msg)
        self.status = "done"
        self._stop = True

    async def _book(self) -> tuple[list[Level], list[Level]]:
        raw = await self.ex.get_order_book(self.cfg.symbol)
        try:
            from app.infrastructure.exchange.wallex.mapper import map_order_book

            b = map_order_book(raw, symbol=self.cfg.symbol)
        except Exception:
            b = raw
        get = (lambda k: b.get(k)) if isinstance(b, dict) else (lambda k: getattr(b, k, None))
        return _levels(get("bids")), _levels(get("asks"))

    # ---------- سفارش ----------
    async def _refresh_own(self) -> None:
        if self.own is None or self.cfg.dry_run:
            return
        orders = await self.ex.get_orders(symbol=self.cfg.symbol, status=None)
        o = next((x for x in orders if x.client_id == self.own.client_id), None)
        if o is None:
            return
        ex_q = Decimal(str(o.executed_qty))
        if getattr(o, "is_open", True):
            self.own.executed = ex_q
        else:
            self.filled += ex_q
            self._note(f"سفارش {o.client_id} بسته شد (اجراشده: {ex_q})")
            self.own = None

    async def _cancel_own(self) -> None:
        o = self.own
        if o is None:
            return
        if self.cfg.dry_run:
            self._note(f"[شبیه‌سازی] لغو سفارش در {o.price}")
            self.own = None
            return
        try:
            res = await self.ex.cancel_order(o.client_id, self.cfg.symbol)
        except Exception:
            try:
                await self._refresh_own()  # شاید همین الان پر شده
            except Exception:
                pass
            raise
        ex_q = getattr(res, "executed_qty", None)
        self.filled += Decimal(str(ex_q)) if ex_q is not None else o.executed
        self._note(f"لغو شد: {o.client_id} (اجراشده: {ex_q})")
        self.own = None

    async def _place(self, price: Decimal) -> None:
        c = self.cfg
        qty = floor_step(self._need(), getattr(self.market, "step_size", None))
        mn = getattr(self.market, "min_notional", None)
        if mn and qty * price < mn:
            self._done("باقی‌مانده کمتر از حداقل ارزش سفارش است")
            return
        if c.max_notional and qty * price > c.max_notional:
            raise ValueError(f"ارزش سفارش ({qty * price}) از سقف مجاز ({c.max_notional}) بیشتر است")
        self.seq += 1
        cid = f"chase-{self.id}-{self.seq}"
        if c.dry_run:
            self._note(f"[شبیه‌سازی] می‌گذاشتم: {c.side} {qty} @ {price}")
        else:
            await self.ex.place_order(
                OrderRequest(
                    symbol=c.symbol, side=OrderSide(c.side), type=OrderType.LIMIT,
                    quantity=qty, price=price, client_id=cid,
                )
            )
            self._note(f"ثبت شد: {c.side} {qty} @ {price} ({cid})")
        self.own = _Own(cid, price, qty)

    # ---------- یک چرخه ----------
    async def step(self) -> None:
        c = self.cfg
        if not c.dry_run and not self.can_trade():
            self._note("معامله واقعی غیرفعال است؛ ربات متوقف شد")
            self.status = "error"
            self._stop = True
            return
        if self.market is None:
            self.market = await self.ex.get_market(c.symbol)
        await self._refresh_own()
        if self._dust(self._need()):
            self._done("هدف کامل شد")
            return

        bids, asks = await self._book()
        own_rem = (self.own.qty - self.own.executed) if (self.own and not c.dry_run) else Decimal(0)
        d = decide(
            c.side, bids, asks, c.low, c.high, self._tick(),
            own_price=self.own.price if self.own else None, own_qty=own_rem,
            min_move_ticks=c.min_move_ticks, enforce_bound=c.enforce_bound,
        )
        self.last_action, self.last_reason = d.action.value, d.reason
        key = (d.action, d.price, d.reason)
        if key != self._last_key:
            self._note(f"{d.action.value}: {d.reason}" + (f" @ {d.price}" if d.price else ""))
            self._last_key = key

        if d.action == Action.PLACE:
            await self._place(d.price)
        elif d.action == Action.MOVE:
            if self.moves >= c.max_moves:
                await self._cancel_own()
                self._note("به سقف تعداد جابه‌جایی رسید")
                self.status = "limit"
                self._stop = True
                return
            await self._cancel_own()
            if self._dust(self._need()):
                self._done("پس از لغو، باقی‌مانده کمتر از حداقل است")
                return
            await self._place(d.price)
            self.moves += 1
        elif d.action == Action.CANCEL:
            await self._cancel_own()

    # ---------- حلقه ----------
    async def run(self) -> None:
        try:
            while not self._stop:
                if time.time() >= self.deadline_at:
                    self._note("مهلت تمام شد")
                    self.status = "expired"
                    break
                try:
                    await self.step()
                    self.errors = 0
                except Exception as e:  # noqa: BLE001
                    self.errors += 1
                    self._note(f"خطا ({self.errors}/{self.cfg.max_errors}): {e}")
                    log.exception("chase step failed")
                    if self.errors >= self.cfg.max_errors:
                        self.status = "error"
                        break
                if self._stop:
                    break
                try:
                    await asyncio.wait_for(self._wake.wait(), timeout=self.cfg.interval_sec)
                except asyncio.TimeoutError:
                    pass
        finally:
            try:
                await self._cancel_own()
            except Exception as e:  # noqa: BLE001
                self._note(f"هشدار: لغو نهایی ناموفق بود: {e}")
            if self.status == "running":
                self.status = "stopped"
                self._note("متوقف شد")

    def start(self) -> None:
        self._task = asyncio.create_task(self.run())

    async def stop(self) -> None:
        self._stop = True
        self._wake.set()
        if self._task:
            try:
                await asyncio.wait_for(asyncio.shield(self._task), timeout=30)
            except Exception:  # noqa: BLE001
                pass

    def snapshot(self) -> dict:
        c = self.cfg
        return {
            "id": self.id, "symbol": c.symbol, "side": c.side, "status": self.status,
            "dry_run": c.dry_run, "low": str(c.low), "high": str(c.high),
            "quantity": str(c.quantity), "filled": str(self.filled), "moves": self.moves,
            "own_price": str(self.own.price) if self.own else None,
            "last_action": self.last_action, "last_reason": self.last_reason,
            "errors": self.errors, "started_at": self.started_at, "deadline_at": self.deadline_at,
            "max_notional": str(c.max_notional) if c.max_notional else None,
            "log": list(self.log)[-30:],
        }


class ChaseManager:
    MAX_ACTIVE = 3

    def __init__(self) -> None:
        self.items: dict[str, ChaseWorker] = {}

    def active(self) -> list[ChaseWorker]:
        return [w for w in self.items.values() if w.status == "running"]

    def create(self, cfg: ChaseConfig, exchange: Any, can_trade: Callable[[], bool], market: Any) -> ChaseWorker:
        act = self.active()
        if any(w.cfg.symbol == cfg.symbol and w.cfg.side == cfg.side for w in act):
            raise ValueError("روی همین نماد و سمت یک تعقیب فعال وجود دارد")
        if len(act) >= self.MAX_ACTIVE:
            raise ValueError(f"حداکثر {self.MAX_ACTIVE} تعقیب هم‌زمان مجاز است")
        w = ChaseWorker(cfg, exchange, can_trade, market)
        self.items[w.id] = w
        w.start()
        for old in [k for k, v in self.items.items() if v.status != "running"][:-20]:
            self.items.pop(old, None)
        return w

    async def stop(self, chase_id: str) -> ChaseWorker | None:
        w = self.items.get(chase_id)
        if w:
            await w.stop()
        return w

    async def stop_all(self) -> None:
        await asyncio.gather(*(w.stop() for w in self.active()), return_exceptions=True)


manager = ChaseManager()
